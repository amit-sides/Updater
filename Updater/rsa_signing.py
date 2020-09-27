from Crypto.PublicKey import RSA

from Updater import registry
from Updater import settings


def sign(data, private_key=None, n=None):
    if private_key is None:
        private_key = int(registry.get_value(settings.RSA_PRIVATE_REGISTRY), 16)
    if n is None:
        n = int(registry.get_value(settings.RSA_MODULO_REGISTRY), 16)

    calculated_hash = int.from_bytes(settings.HASH_MODULE(data).digest(), byteorder='big')
    signature = pow(calculated_hash, private_key, n)
    return signature


def sign_hash(hash_object, private_key=None, n=None):
    if private_key is None:
        private_key = int(registry.get_value(settings.RSA_PRIVATE_REGISTRY), 16)
    if n is None:
        n = int(registry.get_value(settings.RSA_MODULO_REGISTRY), 16)

    calculated_hash = int.from_bytes(hash_object.digest(), byteorder='big')
    signature = pow(calculated_hash, private_key, n)
    return signature


def validate(data, signature, public_key=None, n=None):
    if public_key is None:
        public_key = int(registry.get_value(settings.RSA_PUBLIC_REGISTRY), 16)
    if n is None:
        n = int(registry.get_value(settings.RSA_MODULO_REGISTRY), 16)

    calculated_hash = int.from_bytes(settings.HASH_MODULE(data).digest(), byteorder='big')
    hash_from_signature = pow(signature, public_key, n)
    return calculated_hash == hash_from_signature


def validate_hash(hash_object, signature, public_key=None, n=None):
    if public_key is None:
        public_key = int(registry.get_value(settings.RSA_PUBLIC_REGISTRY), 16)
    if n is None:
        n = int(registry.get_value(settings.RSA_MODULO_REGISTRY), 16)

    calculated_hash = int.from_bytes(hash_object.digest(), byteorder='big')
    hash_from_signature = pow(signature, public_key, n)
    return calculated_hash == hash_from_signature
