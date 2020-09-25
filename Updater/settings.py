import os
import hashlib
import json
import logging

PROGRAM_FILES = os.environ["ProgramFiles"]
HASH_MODULE = hashlib.sha512

__values__ = dict(SOFTWARE_NAME="X",
                  PROGRAM="ex.exe",
                  UPDATER_NAME="Updater",
                  LAUNCHER_NAME="launcher.exe",
                  RSA_KEY_SIZE=1024,  # in bits
                  MESSAGE_SIZE=50,
                  VERSION_CHUNK_SIZE=1460,  # MTU - Headers size (assuming MTU=1500)
                  CONNECTION_TIMEOUT=10,
                  UPDATE_REGISTRY_FORMAT="Update_{}",

                  # Default registry values
                  AUTO_INSTALLATIONS=0,
                  UPDATING_SERVER="127.0.0.1",
                  PORT=77777,
                  UPDATE_MAJOR=1,
                  UPDATE_MINOR=0,
                  VERSION_MAJOR=1,
                  VERSION_MINOR=0,
                  ADDRESS_ID=1,
                  )

__values__.update(dict(
                    # Signature is also used as crc32 sometimes, so it needs to be at least 4 bytes long
                    SIGNATURE_SIZE=max(__values__['RSA_KEY_SIZE'] / 8, 4),  # in bytes
                    ))


def init_settings(save=True):
    global __values__

    __values__.update(dict(
        # Dynamic settings (created automatically by the settings above)

        REGISTRY_PATH=rf"Software\{__values__['SOFTWARE_NAME']}\{__values__['UPDATER_NAME']}",
        SOFTWARE_PATH=rf"{PROGRAM_FILES}{os.path.sep}{__values__['SOFTWARE_NAME']}",
    ))

    __values__.update(dict(
        # Dynamic settings (created automatically by the settings above)

        UPDATER_PATH=rf"{__values__['SOFTWARE_PATH']}{os.path.sep}{__values__['UPDATER_NAME']}",
        LAUNCHER_PATH=rf"{__values__['SOFTWARE_PATH']}{os.path.sep}{__values__['LAUNCHER_NAME']}",
    ))

    __values__.update(dict(
        # Dynamic settings (created automatically by the settings above)

        SETTINGS_PATH=rf"{__values__['UPDATER_PATH']}{os.path.sep}settings.json",
        LOGGER_PATH=rf"{__values__['UPDATER_PATH']}{os.path.sep}log.txt",
        UPDATE_PATH=rf"{__values__['UPDATER_PATH']}{os.path.sep}update.zip",

        AUTO_INSTALLATIONS_REGISTRY=rf"{__values__['REGISTRY_PATH']}\auto_update",
        UPDATING_SERVER_REGISTRY=rf"{__values__['REGISTRY_PATH']}\update_server",
        PORT_REGISTRY=rf"{__values__['REGISTRY_PATH']}\port",
        RSA_MODULO_REGISTRY=rf"{__values__['REGISTRY_PATH']}\rsa_modulo",
        RSA_PUBLIC_REGISTRY=rf"{__values__['REGISTRY_PATH']}\rsa_public",
        RSA_PRIVATE_REGISTRY=rf"{__values__['REGISTRY_PATH']}\rsa_private",
        UPDATE_MAJOR_REGISTRY=rf"{__values__['REGISTRY_PATH']}\update_major",
        UPDATE_MINOR_REGISTRY=rf"{__values__['REGISTRY_PATH']}\update_minor",
        VERSION_MAJOR_REGISTRY=rf"{__values__['REGISTRY_PATH']}\version_major",
        VERSION_MINOR_REGISTRY=rf"{__values__['REGISTRY_PATH']}\version_minor",
        ADDRESS_ID_REGISTRY=rf"{__values__['REGISTRY_PATH']}\address_id",
    ))

    load_settings()
    if save:
        save_settings()


def load_settings():
    global __values__

    try:
        with open(__values__['SETTINGS_PATH'], "r") as settings_file:
            data = settings_file.read()
            __values__.update(json.loads(data))
    except FileNotFoundError:
        # If settings file is not found, use default settings
        pass


def save_settings():
    global __values__

    try:
        with open(__values__['SETTINGS_PATH'], "w") as settings_file:
            data = json.dumps(__values__)
            settings_file.write(data)
    except PermissionError:
        logging.critical(f"Failed to write settings file due to PermissionError: {__values__['SETTINGS_PATH']}")


def __getattr__(name):
    global __values__

    if name in __values__:
        return __values__[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
