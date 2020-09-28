import os
import sys
import json
import zipfile
import construct
import argparse

import validators
from Crypto.PublicKey import RSA

sys.path.append("..")

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
    return dict()


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
        return False

    # Adds the keys to registry
    registry.set_value(settings.RSA_MODULO_REGISTRY, hex(key_pair.n))
    registry.set_value(settings.RSA_PUBLIC_REGISTRY, hex(key_pair.e))
    registry.set_value(settings.RSA_PRIVATE_REGISTRY, hex(key_pair.d))

    # Displays the keys to the user
    print("RSA keys were generated!")
    print("")
    show_rsa_keys()
    return True


def show_rsa_keys():
    print("RSA Modulo (n):")
    if registry.exists(settings.RSA_MODULO_REGISTRY):
        print(registry.get_value(settings.RSA_MODULO_REGISTRY))
    else:
        print("Not available.")
    print("")

    print("RSA Public Key (e):")
    if registry.exists(settings.RSA_PUBLIC_REGISTRY):
        print(registry.get_value(settings.RSA_PUBLIC_REGISTRY))
    else:
        print("Not available.")
    print("")

    print("RSA Private Key (d):")
    if registry.exists(settings.RSA_PRIVATE_REGISTRY):
        print(registry.get_value(settings.RSA_PRIVATE_REGISTRY))
    else:
        print("Not available.")
    return True


def show_server_information():
    address_id = "Not available"
    if registry.exists(settings.ADDRESS_ID_REGISTRY):
        address_id = registry.get_value(settings.ADDRESS_ID_REGISTRY)

    ip = "Not available"
    if registry.exists(settings.UPDATING_SERVER_REGISTRY):
        ip = registry.get_value(settings.UPDATING_SERVER_REGISTRY)

    port = "Not available"
    if registry.exists(settings.PORT_REGISTRY):
        port = registry.get_value(settings.PORT_REGISTRY)

    print(f"Address ID: \t{address_id}")
    print(f"Domain (IP): \t{ip}")
    print(f"Port: \t\t{port}")
    return True


def send_server_information(ip, port, spread=True):
    # Validates the ip or domain (syntax only)
    if validators.domain(ip) is not True:
        if validators.ip_address.ipv4(ip) is not True:
            if validators.ip_address.ipv6(ip) is not True:
                print(f"Failed to validate ip or domain: {ip}. Check for typing mistakes.")
                return False

    # Validates port number
    if validators.between(port, min=1, max=65535) is not True:
        print(f"Invalid port number: {port} is not between 1 and 65535")
        return False

    if not registry.exists(settings.ADDRESS_ID_REGISTRY):
        print(f"Address ID was not found in the registry! (Location: {settings.ADDRESS_ID_REGISTRY})")
        return False
    if not registry.exists(settings.RSA_PRIVATE_REGISTRY):
        print(f"RSA Private Key was not found in the registry! (Location: {settings.RSA_PRIVATE_REGISTRY})")
        return False
    address_id = registry.get_value(settings.ADDRESS_ID_REGISTRY)

    # Creates server message
    server_update_dict = dict(
        type=MessageType.SERVER_UPDATE,
        signature=0,
        address_id=address_id + 1,  # Increases the address id, to indicate the information is new and up to date.
        address_size=len(ip),
        address=ip.encode("ascii"),
        port=port,
        spread=spread
    )

    # Calculate signature of message
    try:
        server_update_message = constructs.SERVER_UPDATE_MESSAGE.build(server_update_dict)

        # Update signature
        server_update_dict["signature"] = constructs.sign_message(server_update_message)
        server_update_message = constructs.SERVER_UPDATE_MESSAGE.build(server_update_dict)
    except construct.ConstructError as e:
        # Should never occur
        print(f"Failed to build server update message: {e.args}")
        return False

    # Sends server information update (should also update local server information)
    updater.send_broadcast(server_update_message)
    print("Server information was sent to services!")
    return True


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
        update_zip.close()

    # Updating registry with update info
    version_registry = version.get_update_registry_path()
    registry.set_value(version_registry, os.path.abspath(update_filepath))
    version.update_current_version()

    print(f"Created update version {version} successfully!")
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
        version_update_message = constructs.VERSION_UPDATE_MESSAGE.build(version_update_dict)

        # Update signature
        version_update_dict["header_signature"] = constructs.sign_message(version_update_message)
        print(f"Spread: {version_update_dict['spread']}")
        version_update_message = constructs.VERSION_UPDATE_MESSAGE.build(version_update_dict)
    except construct.ConstructError:
        # Should never occur
        print(f"Failed to build request update message")
        return False

    # Sends the message
    updater.send_broadcast(version_update_message)
    # After the update is announced, the service will send it to the clients, when they ask for it
    print(f"Broadcast was sent with version {update_version} !")
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

    # Parse everything
    args = parser.parse_args()

    # Initialize settings
    settings.init_settings(save=False)

    # call command function
    try:
        func = args.func
    except AttributeError:
        print(f"Invalid command. Run with `{sys.argv[0]} -h` for usage.")
        return
    del args.func
    func(**vars(args))


if __name__ == "__main__":
    main()


