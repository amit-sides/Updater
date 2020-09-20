import os
import hashlib
import json
import logging

values = dict()


def init_settings():
    global values

    values.update(dict(
        SOFTWARE_NAME="X",
        UPDATER_NAME="Updater",
        LAUNCHER_NAME="launcher.exe",
        RSA_KEY_SIZE=1024,  # in bits
        MESSAGE_SIZE=50,
        VERSION_CHUNK_SIZE=1460,  # MTU - Headers size (assuming MTU=1500)
        CONNECTION_TIMEOUT=10,
        HASH_MODULE=hashlib.sha512,
    ))

    values.update(dict(
        # Dynamic settings (created automatically by the settings above)

        REGISTRY_PATH=rf"Software\{values['SOFTWARE_NAME']}\{values['UPDATER_NAME']}",
        SOFTWARE_PATH=rf"%ProgramFiles%{os.path.sep}{values['SOFTWARE_NAME']}",
        UPDATER_PATH=rf"%ProgramFiles%{os.path.sep}{values['UPDATER_NAME']}",
        LAUNCHER_PATH=rf"%ProgramFiles%{os.path.sep}{values['LAUNCHER_NAME']}",
        SETTINGS_PATH=rf"{values['UPDATER_PATH']}{os.path.sep}settings.json",

        # Signature is also used as crc32 sometimes, so it needs to be at least 4 bytes long
        SIGNATURE_SIZE=max(values['RSA_KEY_SIZE'] / 8, 4),  # in bytes
    ))

    values.update(dict(
        # Dynamic settings (created automatically by the settings above)

        LOGGER_PATH=rf"{values['UPDATER_PATH']}{os.path.sep}log.txt",
    ))

    load_settings()
    save_settings()


def load_settings():
    global values

    try:
        with open(values['SETTINGS_PATH'], "r") as settings_file:
            data = settings_file.read()
            values.update(json.loads(data))
    except FileNotFoundError:
        # If settings file is not found, use default settings
        pass


def save_settings():
    global values

    try:
        with open(values['SETTINGS_PATH'], "w") as settings_file:
            data = json.dumps(values)
            settings_file.write(data)
    except PermissionError:
        logging.critical(f"Failed to write settings file due to PermissionError: {values['SETTINGS_PATH']}")


def __getattr__(name):
    global values

    if name in values:
        return values[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
