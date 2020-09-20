import os
import hashlib
import json
import logging

__values__ = dict()


def init_settings():
    global __values__

    __values__.update(dict(
        SOFTWARE_NAME="X",
        PROGRAM="ex.exe",
        UPDATER_NAME="Updater",
        LAUNCHER_NAME="launcher.exe",
        RSA_KEY_SIZE=1024,  # in bits
        MESSAGE_SIZE=50,
        VERSION_CHUNK_SIZE=1460,  # MTU - Headers size (assuming MTU=1500)
        CONNECTION_TIMEOUT=10,
        HASH_MODULE=hashlib.sha512,
        UPDATE_REGISTRY_FORMAT="Update_{}",
    ))

    __values__.update(dict(
        # Dynamic settings (created automatically by the settings above)

        REGISTRY_PATH=rf"Software\{__values__['SOFTWARE_NAME']}\{__values__['UPDATER_NAME']}",
        SOFTWARE_PATH=rf"%ProgramFiles%{os.path.sep}{__values__['SOFTWARE_NAME']}",
        UPDATER_PATH=rf"%ProgramFiles%{os.path.sep}{__values__['UPDATER_NAME']}",
        LAUNCHER_PATH=rf"%ProgramFiles%{os.path.sep}{__values__['LAUNCHER_NAME']}",
        SETTINGS_PATH=rf"{__values__['UPDATER_PATH']}{os.path.sep}settings.json",

        # Signature is also used as crc32 sometimes, so it needs to be at least 4 bytes long
        SIGNATURE_SIZE=max(__values__['RSA_KEY_SIZE'] / 8, 4),  # in bytes
    ))

    __values__.update(dict(
        # Dynamic settings (created automatically by the settings above)

        LOGGER_PATH=rf"{__values__['UPDATER_PATH']}{os.path.sep}log.txt",
        UPDATE_PATH=rf"{__values__['UPDATER_PATH']}{os.path.sep}update.zip",

        AUTO_INSTALLATIONS_REGISTRY=rf"{__values__['REGISTRY_PATH']}\auto_update"
    ))

    load_settings()
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
