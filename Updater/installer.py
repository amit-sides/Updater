
import os
import json
from Crypto.PublicKey import RSA

from Updater import settings


def create_basic_settings_file():
    settings.init_settings(save=False)
    key_pair = RSA.generate(bits=settings.RSA_KEY_SIZE)

    basic_settings = dict(
        RSA_MODULO=hex(key_pair.n),
        PUBLIC_KEY=hex(key_pair.e),

        UPDATE_MAJOR=1,
        UPDATE_MINOR=0,
        VERSION_MAJOR=1,
        VERSION_MINOR=0,
    )

    name = os.path.basename(settings.SETTINGS_PATH)
    with open(name, "w") as settings_file:
        data = json.dumps(basic_settings)
        settings_file.write(data)

    print(f"Created {name}")

