
import os
import json
import zipfile
import construct
import argparse
from Crypto.PublicKey import RSA

from Updater import settings
from Updater import registry
from Updater import rsa_signing
from Updater import updater
from Updater import constructs
from Updater.constructs import MessageType

DEFAULT_SETTINGS_PATH = "settings.json"


def load_settings():
    try:
        with open(DEFAULT_SETTINGS_PATH, "r") as settings_file:
            data = settings_file.read()
            return json.loads(data)
    except FileNotFoundError:
        # If settings file is not found, use default settings
        pass
    return None


def save_settings(values):
    try:
        with open(DEFAULT_SETTINGS_PATH, "w") as settings_file:
            data = json.dumps(values)
            settings_file.write(data)
    except PermissionError:
        return False
    return True


def add_to_settings(values):
    current_settings = load_settings()
    if current_settings is None:
        return False

    current_settings.update(values)
    return save_settings(current_settings)


def zip_directory(path, zip_handler):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, path)
            zip_handler.write(file_path, relative_path)

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            relative_path = os.path.relpath(dir_path, path)
            zip_handler.write(dir_path, relative_path)


def generate_rsa_keys():
    key_pair = RSA.generate(bits=settings.RSA_KEY_SIZE)

    # Adds the keys to settings file
    rsa_settings = dict(
        RSA_MODULO=hex(key_pair.n),
        PUBLIC_KEY=hex(key_pair.e),
    )
    if not add_to_settings(rsa_settings):
        print(f"Failed to add rsa key to {DEFAULT_SETTINGS_PATH}")

    # Adds the keys to registry
    registry.set_value(settings.RSA_MODULO_REGISTRY, hex(key_pair.n))
    registry.set_value(settings.RSA_PUBLIC_REGISTRY, hex(key_pair.e))
    registry.set_value(settings.RSA_PRIVATE_REGISTRY, hex(key_pair.d))


def show_rsa_keys():
    pass


def show_server_information():
    pass


def send_server_information(ip, port):
    # Check validation of IP and port!!!
    pass


def create_update(update_path, major, minor):
    version = updater.Version(major, minor)

    # Tries to open update file (might fail if clients are downloading it)
    try:
        update_filepath = settings.UPDATE_PATH
        update_filepath = f"{update_filepath}.{version}"
        update_file = open(update_filepath, "wb")
    except PermissionError:
        print(f"Failed to write update file {settings.UPDATE_PATH}. Insufficient permission or file is locked.")
        return False

    # Creating update zip
    with update_file:
        update_zip = zipfile.ZipFile(update_file, "w")
        zip_directory(update_path, update_zip)

    # Updating registry with update info
    version_registry = version.get_update_registry_path()
    registry.set_value(version_registry, os.path.abspath(update_filepath))
    version.update_current_version()
    return True


def broadcast_update_version(spread=True):
    # Gets the update info and update file
    update_version = updater.Version.get_current_version()
    version_registry = update_version.get_update_registry_path()
    update_filepath = registry.get_value(version_registry)

    # Tries to open update file (might fail if clients are downloading it)
    try:
        file_size = os.stat(update_filepath).st_size
        update_file = open(update_filepath, "rb")
    except PermissionError:
        print(f"Failed to write update file {settings.UPDATE_PATH}. Insufficient permission or file is locked.")
        return False

    # Calculates size and signature of update
    data_received = 0
    hash_object = settings.HASH_MODULE()

    # Calculate update signature
    with update_file:
        while data_received < file_size:
            chunk = update_file.read(settings.VERSION_CHUNK_SIZE)
            hash_object.update(chunk)
            data_received += len(chunk)
    signature = rsa_signing.sign_hash(hash_object)

    # Creates broadcast message
    version_update_dict = dict(
        type=MessageType.VERSION_UPDATE,
        header_signature=0,
        major=update_version.major,
        minor=update_version.minor,
        size=file_size,
        update_signature=signature,
        spread=spread
    )

    # Calculate signature of message
    try:
        version_update_message = constructs.REQUEST_UPDATE_MESSAGE.build(version_update_dict)

        # Update signature
        version_update_dict["header_signature"] = constructs.sign_message(version_update_message)
        version_update_message = constructs.REQUEST_UPDATE_MESSAGE.build(version_update_dict)
    except construct.ConstructError:
        # Should never occur
        print(f"Failed to build request update message")
        return False

    # Sends the message
    updater.send_broadcast(version_update_message)
    # After the update is announced, the service will send it to the clients, when they ask for it
    return True


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Top level commands
    rsa_group = subparsers.add_parser("rsa")
    update_group = subparsers.add_parser("update")
    server_group = subparsers.add_parser("server")

    # Sub-commands of rsa

    subparsers = rsa_group.add_subparsers()
    # generate
    rsa_generate = subparsers.add_parser("generate")
    rsa_generate.set_defaults(func=generate_rsa_keys)
    # show
    rsa_show = subparsers.add_parser("show")
    rsa_show.set_defaults(func=show_rsa_keys)

    # Sub-commands of update

    subparsers = update_group.add_subparsers()
    # create
    update_create = subparsers.add_parser("create")
    update_create.add_argument("update_path", metavar="<Path to Update Folder>", type=str,
                              help="The path to the update folder (folder content will be compressed to zip).")
    update_create.add_argument("major", metavar="<major>", type=int,
                               help="The major number of the version.")
    update_create.add_argument("minor", metavar="<minor>", type=int,
                               help="The minor number of the version.")
    update_create.set_defaults(func=create_update)

    # broadcast
    update_broadcast = subparsers.add_parser("broadcast")
    update_broadcast.add_argument("-s", "--spread", action="store_true",
                        help="Sets 'spread' bit flag in broadcast message, will tell other clients to forward this message.")
    update_broadcast.set_defaults(func=broadcast_update_version)

    # Sub-commands of server

    subparsers = server_group.add_subparsers()
    # show
    server_show = subparsers.add_parser("show")
    server_show.set_defaults(func=show_server_information)
    # update
    server_update = subparsers.add_parser("update")
    server_update.add_argument("ip", metavar="<ip or domain>", type=str,
                               help="The ip or the domain of the update server.")
    server_update.add_argument("port", metavar="<port>", type=int,
                               help="The port that the updating service will listen on.")
    server_update.add_argument("-s", "--spread", action="store_true",
                                  help="Sets 'spread' bit flag in broadcast message, will tell other clients to forward this message.")
    server_update.set_defaults(func=send_server_information)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


