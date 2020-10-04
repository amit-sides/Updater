import os
import sys
import hashlib
import json
import logging

from Updater import registry

if getattr(sys, 'frozen', False):
    # frozen
    CURRENT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # unfrozen
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

INITIAL_SETTINGS_PATH = f"{CURRENT_DIR}{os.path.sep}settings.json"
PROGRAM_FILES = os.environ["ProgramFiles"]
HASH_MODULE = hashlib.sha512

__values__ = dict(SOFTWARE_NAME="X",
                  PROGRAM="X.exe",
                  UPDATER_NAME="Updater",
                  LAUNCHER_NAME="launcher.exe",
                  RSA_KEY_SIZE=1024,  # in bits
                  VERSION_CHUNK_SIZE=1460,  # MTU - Headers size (assuming MTU=1500)
                  CONNECTION_TIMEOUT=10,

                  # Default registry values
                  AUTO_INSTALLATIONS=0,
                  UPDATING_SERVER="127.0.0.1",
                  PORT=55555,
                  UPDATE_MAJOR=1,
                  UPDATE_MINOR=0,
                  VERSION_MAJOR=1,
                  VERSION_MINOR=0,
                  ADDRESS_ID=1,
                  )

__values__.update(dict(
                    # Signature is also used as crc32 sometimes, so it needs to be at least 4 bytes long
                    SIGNATURE_SIZE=max(__values__["RSA_KEY_SIZE"] // 8, 4),  # in bytes
                    ))

__values__.update(dict(
                    MESSAGE_SIZE=__values__["SIGNATURE_SIZE"] * 2 + 50,
                    ))


def init_settings(save=True, load=True):
    global __values__

    # Default settings that are needed before load
    __values__.setdefault("REGISTRY_PATH", rf"Software\{__values__['SOFTWARE_NAME']}\{__values__['UPDATER_NAME']}")
    __values__.setdefault("SETTINGS_REGISTRY", rf"{__values__['REGISTRY_PATH']}\settings")

    # Load existing settings
    if load:
        load_settings()

    # Setting default settings values, if they don't appear in the settings.json file already

    __values__.setdefault("SOFTWARE_PATH", rf"{PROGRAM_FILES}{os.path.sep}{__values__['SOFTWARE_NAME']}")
    __values__.setdefault("UPDATER_PATH", rf"{__values__['SOFTWARE_PATH']}{os.path.sep}{__values__['UPDATER_NAME']}")
    __values__.setdefault("PROGRAM_PATH", rf"{__values__['SOFTWARE_PATH']}{os.path.sep}{__values__['SOFTWARE_NAME']}")
    __values__.setdefault("LAUNCHER_PATH", rf"{__values__['SOFTWARE_PATH']}{os.path.sep}{__values__['LAUNCHER_NAME']}")
    __values__.setdefault("SETTINGS_PATH", rf"{__values__['UPDATER_PATH']}{os.path.sep}settings.json")
    __values__.setdefault("LOGGER_PATH", rf"{__values__['UPDATER_PATH']}{os.path.sep}log.txt")
    __values__.setdefault("UPDATE_PATH", rf"{__values__['UPDATER_PATH']}{os.path.sep}update.zip")
    __values__.setdefault("AUTO_INSTALLATIONS_REGISTRY", rf"{__values__['REGISTRY_PATH']}\auto_update")
    __values__.setdefault("UPDATING_SERVER_REGISTRY", rf"{__values__['REGISTRY_PATH']}\update_server")
    __values__.setdefault("PORT_REGISTRY", rf"{__values__['REGISTRY_PATH']}\port")
    __values__.setdefault("RSA_MODULO_REGISTRY", rf"{__values__['REGISTRY_PATH']}\rsa_modulo")
    __values__.setdefault("RSA_PUBLIC_REGISTRY", rf"{__values__['REGISTRY_PATH']}\rsa_public")
    __values__.setdefault("RSA_PRIVATE_REGISTRY", rf"{__values__['REGISTRY_PATH']}\rsa_private")
    __values__.setdefault("UPDATE_MAJOR_REGISTRY", rf"{__values__['REGISTRY_PATH']}\update_major")
    __values__.setdefault("UPDATE_MINOR_REGISTRY", rf"{__values__['REGISTRY_PATH']}\update_minor")
    __values__.setdefault("VERSION_MAJOR_REGISTRY", rf"{__values__['REGISTRY_PATH']}\version_major")
    __values__.setdefault("VERSION_MINOR_REGISTRY", rf"{__values__['REGISTRY_PATH']}\version_minor")
    __values__.setdefault("ADDRESS_ID_REGISTRY", rf"{__values__['REGISTRY_PATH']}\address_id")
    __values__.setdefault("UPDATE_REGISTRY_FORMAT", rf"{__values__['REGISTRY_PATH']}\Update_{{}}")

    # Saves the settings, if they should be saved
    if save:
        save_settings()


def load_settings():
    global __values__
    if "SETTINGS_REGISTRY" in __values__ and registry.exists(__values__["SETTINGS_REGISTRY"]):
        settings_path = registry.get_value(__values__["SETTINGS_REGISTRY"])
    else:
        settings_path = __values__["SETTINGS_PATH"] if "SETTINGS_PATH" in __values__ else INITIAL_SETTINGS_PATH

    try:
        with open(settings_path, "r") as settings_file:
            data = settings_file.read()
            __values__.update(json.loads(data))
    except FileNotFoundError:
        # If settings file is not found, use default settings
        pass


def save_settings():
    global __values__
    if "SETTINGS_REGISTRY" in __values__ and registry.exists(__values__["SETTINGS_REGISTRY"]):
        settings_path = registry.get_value(__values__["SETTINGS_REGISTRY"])
    else:
        settings_path = __values__["SETTINGS_PATH"] if "SETTINGS_PATH" in __values__ else INITIAL_SETTINGS_PATH

    try:
        with open(settings_path, "w") as settings_file:
            data = json.dumps(__values__)
            settings_file.write(data)
    except PermissionError:
        logging.critical(f"Failed to write settings file due to PermissionError: {__values__['SETTINGS_PATH']}", exc_info=True)


def __getattr__(name):
    global __values__

    if name in __values__:
        return __values__[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
