
import os
import logging
import socket
import construct
import zlib
import threading
import shutil

import constructs
from constructs import MessageType
import rsa_signing
import settings
import registry


class Version(object):
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    @staticmethod
    def get_current_version():
        major = registry.get_value(settings.UPDATE_MAJOR_REGISTRY)
        minor = registry.get_value(settings.UPDATE_MINOR_REGISTRY)
        return Version(major, minor)

    def update_current_version(self):
        registry.set_value(settings.UPDATE_MAJOR_REGISTRY, self.major)
        registry.set_value(settings.UPDATE_MINOR_REGISTRY, self.minor)

    def get_update_registry_path(self):
        return rf"Update_{self}"

    @staticmethod
    def get_installed_version():
        major = registry.get_value(settings.VERSION_MAJOR_REGISTRY)
        minor = registry.get_value(settings.VERSION_MINOR_REGISTRY)
        return Version(major, minor)

    def update_installed_version(self):
        registry.set_value(settings.VERSION_MAJOR_REGISTRY, self.major)
        registry.set_value(settings.VERSION_MINOR_REGISTRY, self.minor)

    @staticmethod
    def is_updated():
        installed_version = Version.get_installed_version()
        update_version = Version.get_current_version()
        return installed_version >= update_version 

    def __eq__(self, other):
        return self.major == other.major and self.minor == other.minor

    def __gt__(self, other):
        if self.major > other.major:
            return True
        if other.major > self.major:
            return False
        return self.minor > other.minor

    def __ge__(self, other):
        return self > other or self == other

    def __lt__(self, other):
        return other > self

    def __le__(self, other):
        return self < other or self == other

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return f"{self.major}.{self.minor}"


class Updater(object):
    def __init__(self):
        self.message = None
        self.sender = None
        self.management_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.setup_listener()

    def setup_listener(self):
        port = registry.get_value(settings.PORT_REGISTRY)
        self.management_socket.bind(("0.0.0.0", port))

    def broadcast_message(self):
        broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcaster.settimeout(settings.CONNECTION_TIMEOUT)
        port = registry.get_value(settings.PORT_REGISTRY)

        try:
            # Enable broadcasting mode
            broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Sends the broadcast
            broadcaster.sendto(self.message, ("<broadcast>", port))

        except socket.error:
            logging.error("Unknown error while sending broadcast :(")
        finally:
            broadcaster.shutdown(2)
            broadcaster.close()

    def receive_message(self):
        try:
            message, sender = self.management_socket.recvfrom(settings.MESSAGE_SIZE)
        except socket.error:
            logging.info("Failed to receive message on management socket.")
            message = sender = None

        if len(message) != settings.MESSAGE_SIZE:
            logging.info(f"Received message with incorrect size: received {len(message)} expected {settings.MESSAGE_SIZE}")
            message = sender = None

        self.message = message
        self.sender = sender

    def handle_message(self):
        if len(self.message) != settings.MESSAGE_SIZE:
            # Invalid message length
            logging.error(f"Received an invalid message length: {len(self.message)}")
            return

        # Parse the message
        try:
            message = constructs.GENERIC_MESSAGE.parse(self.message)
        except construct.ConstructError:
            logging.error(f"Failed to parse message with length: {len(self.message)}")
            return

        if len(MessageType) < int(message.type):
            # Invalid message type, ignoring...
            logging.warning(f"Received an invalid message type {message.type}")
            return

        message_type = int(message.type)
        # These messages don't require authentication (they are created by the clients)
        # In these messages the 'signature' is nothing but a CRC32 checksum
        if message_type == MessageType.REQUEST_UPDATE_MESSAGE:
            calculated_checksum = zlib.crc32(message.data)
            if calculated_checksum != message.signature:
                # Invalid checksum, ignore message...
                logging.info(f"Received a message with incorrect checksum. received {hex(message.signature)} expected {hex(calculated_checksum)}.")
                return

            update_sender = threading.Thread(target=Updater.send_version_update, args=(self.message, self.sender))
            update_sender.setDaemon(True)
            update_sender.start()
            return

        # Validates the message signature
        if not rsa_signing.validate(message.data, message.signature):
            # Could be either an error in the message or an attacker tampered message
            logging.warning(f"Invalid signature: {hex(message.signature)}")
            return

        # Handle message
        if message_type == MessageType.SERVER_UPDATE:
            self.handle_server_update()
        elif message_type == MessageType.VERSION_UPDATE:
            self.handle_version_update()
        else:
            # Unimplemented message type, probably an error...
            logging.error(f"Received an unimplemented message type {message_type}")

    def handle_server_update(self):
        if len(self.message) != constructs.SERVER_UPDATE_MESSAGE.sizeof():
            # The message has an incorrect size...
            logging.warning(f"Incorrect message size: {len(self.message)}")
            return

        # Parse the message
        try:
            message = constructs.SERVER_UPDATE_MESSAGE.parse(self.message)
        except construct.ConstructError:
            # Should never occur
            logging.critical(f"Failed to parse server update message: {self.message.hex()}")
            return

        # Check the running id is more updated than the current id
        current_id = registry.get_value(settings.ADDRESS_ID_REGISTRY)
        if current_id >= message.address_id:
            # An outdated message, should ignore...
            logging.info(f"Received an outdated server update message. current id: {current_id}, received id: {message.address_id}.")
            return

        # The message is updated, update our data!
        registry.set_value(settings.UPDATING_SERVER_REGISTRY, message.address)
        registry.set_value(settings.PORT_REGISTRY, message.port)
        registry.set_value(settings.ADDRESS_ID_REGISTRY, message.address_id)
        logging.info(f"Updated address to {message.address} and port to {message.port}")

        # Since port could have changed, we restart our socket
        self.cleanup_listener()
        self.setup_listener()

        # Checks if the sender requested to spread this message using broadcast
        if message.spread:
            self.broadcast_message()

    def handle_version_update(self):
        if len(self.message) != constructs.VERSION_UPDATE_MESSAGE.sizeof():
            # The message has an incorrect size...
            logging.warning(f"Incorrect message size: {len(self.message)}")
            return

        # Parse the message
        try:
            message = constructs.VERSION_UPDATE_MESSAGE.parse(self.message)
        except construct.ConstructError:
            # Should never occur
            logging.critical(f"Failed to parse server update message: {self.message.hex()}")
            return

        # Check the version is not an outdated version
        update_version = Version(message.major, message.minor)
        current_version = Version.get_current_version()
        if current_version >= update_version:
            # An outdated version, should ignore...
            logging.info(f"Received an outdated version update message. current version: {current_version}, update version: {update_version}.")
            return

        # The version contains an update! download it!
        if self.download_update(message):
            # The version was downloaded successfully, install if necessary
            self.handle_installation()

            # Checks if the sender requested to spread this message using broadcast
            if message.spread:
                self.broadcast_message()

    def download_update(self, message):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Creates the TCP server that receives the update
            listener.settimeout(settings.CONNECTION_TIMEOUT)
            listener.bind(("0.0.0.0", 0))  # Bind to random port
            port = listener.getsockname()[1]
            listener.listen(1)

            # Build the request version message
            requested_version = Version(message.major, message.minor)
            request_version_dict =  dict(
                                        type=MessageType.REQUEST_UPDATE,
                                        crc32=0,
                                        listening_port=port,
                                        major=requested_version.major,
                                        minor=requested_version.minor
                                    )
            try:
                request_version_message = constructs.REQUEST_UPDATE_MESSAGE.build(request_version_dict)

                # Update CRC32
                request_version_dict["crc32"] = constructs.calculate_crc(request_version_message)
                request_version_message = constructs.REQUEST_UPDATE_MESSAGE.build(request_version_dict)
            except construct.ConstructError:
                # Should never occur
                logging.critical(f"Failed to build request update message")
                return False

            # Creating the file for the update
            update_filepath = registry.get_value(settings.EXECUTABLE_PATH)
            update_filepath = f"{update_filepath}.{requested_version}"
            update_file = open(update_filepath, "wb")

            # Request the update (so that the Updater will connect to our listening socket)
            port = registry.get_value(settings.PORT_REGISTRY)
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.sendto(request_version_message, 0, (self.sender[0], port))
            temp_socket.shutdown(2)
            temp_socket.close()

            # Awaits for sender to connect
            receiver, _ = listener.accept()
            receiver.settimeout(settings.CONNECTION_TIMEOUT)
            data_received = 0
            hash_object = settings.HASH_MODULE()

            # Download the update
            with update_file:
                while data_received < message.size:
                    chunk = receiver.recv(settings.VERSION_CHUNK_SIZE)
                    update_file.write(chunk)
                    hash_object.update(chunk)
                    data_received += len(chunk)

            # Close the TCP connection
            receiver.shutdown(2)
            receiver.close()

            # Validate the update signature
            if not rsa_signing.validate_hash(hash_object, message.update_signature):
                # Delete this invalid update file
                os.remove(update_filepath)
                logging.info("Invalid signature for update file (maybe tampered?)")
                return False

            # Update the registry with the current update
            version_registry = requested_version.get_update_registry_path()
            registry.set_value(version_registry, os.path.abspath(update_filepath))
            requested_version.update_current_version()

        except socket.timeout:
            # Connection was timed-out, too bad... abort
            logging.info("Connection timed out")
            return False
        except socket.error:
            # Socket error
            logging.info("Socket error has occurred")
            return False
        finally:
            listener.shutdown(2)
            listener.close()

        return True

    @staticmethod
    def handle_installation():
        # Checks if an update is available
        if Version.is_updated():
            return True

        # Checks if the update should be installed automatically
        automatic_installation = registry.get_value(settings.AUTO_INSTALLATIONS)
        if automatic_installation == 0:
            return True

        # Get the path of the installed executable and the update file
        version_registry = Version.get_current_version().get_update_registry_path()
        update_filepath = registry.get_value(version_registry)
        executable_path = settings.EXECUTABLE_PATH

        # Replace the executable with the update file
        try:
            shutil.copy(update_filepath, executable_path)
            # If an error occurred, we ignore it and let the user manually update when they execute the launcher
        except PermissionError:
            logging.info(f"Failed to replace executable {executable_path}. Insufficient permission or file is running.")
            return False
        except OSError:
            logging.error(f"Failed to replace executable {executable_path}. Unknown OS Error.")
            return False

        # Version was updated! Update the registry
        registry.set_value(version_registry, executable_path)
        Version.get_current_version().update_installed_version()

        # Delete the useless update file (might fail but it doesn't really matter)
        try:
            os.remove(update_filepath)
        except OSError:
            logging.info(f"Unable to delete update file {update_filepath}. not too terrible...")
            # Continues...

        return True

    @staticmethod
    def send_version_update(message, requester):
        if len(message) != constructs.REQUEST_UPDATE_MESSAGE.sizeof():
            # The message has an incorrect size...
            logging.warning(f"Incorrect message size: {len(message)}")
            return

        # Parse the message
        try:
            message = constructs.REQUEST_UPDATE_MESSAGE.parse(message)
        except construct.ConstructError:
            # Should never occur
            logging.critical(f"Failed to parse request update message: {message.hex()}")
            return

        # Check if the version file exists
        requested_version = Version(message.major, message.minor)
        version_registry = requested_version.get_update_registry_path()
        if not registry.exists(version_registry):
            # Version not exists... abort
            logging.info(f"Version {requested_version} was requested but wasn't found in the registry")
            return
        
        # Retrieve the update filepath
        version_filepath = registry.get_value(version_registry)
        try:
            update_file = open(version_filepath, "rb")
        except OSError:
            logging.error(f"Unable to open version file: {version_filepath}")
            return

        sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Connect to the TCP server of the receiver
            sender.settimeout(settings.CONNECTION_TIMEOUT)
            sender.connect((requester[0], message.listening_port))

            # Send the update file
            with update_file:
                chunk = update_file.read(settings.VERSION_CHUNK_SIZE)
                while chunk != "":
                    sender.send(chunk)
                    chunk = update_file.read(settings.VERSION_CHUNK_SIZE)

        except socket.timeout:
            # Connection was timed-out, too bad... abort
            logging.info("Connection timed out")
        except socket.error:
            # Socket error
            logging.info("Socket error has occurred")
        finally:
            sender.shutdown(2)
            sender.close()

    def cleanup_listener(self):
        self.management_socket.shutdown(2)
        self.management_socket.close()

    def __del__(self):
        self.cleanup_listener()
