from Crypto.PublicKey import RSA

import registry
import settings


def sign(data, private_key=None, n=None):
    if private_key is None:
        private_key = registry.get_value(settings.PRIVATE_KEY_REGISTRY)
    if n is None:
        n = registry.get_value(settings.MODULO_REGISTRY)

    calculated_hash = int.from_bytes(settings.HASH_MODULE(data).digest(), byteorder='big')
    signature = pow(calculated_hash, private_key, n)
    return signature


def sign_hash(hash_object, private_key=None, n=None):
    if private_key is None:
        private_key = registry.get_value(settings.PRIVATE_KEY_REGISTRY)
    if n is None:
        n = registry.get_value(settings.MODULO_REGISTRY)

    calculated_hash = int.from_bytes(hash_object.digest(), byteorder='big')
    signature = pow(calculated_hash, private_key, n)
    return signature


def validate(data, signature, public_key=None, n=None):
    if public_key is None:
        public_key = registry.get_value(settings.PUBLIC_KEY_REGISTRY)
    if n is None:
        n = registry.get_value(settings.MODULO_REGISTRY)

    calculated_hash = int.from_bytes(settings.HASH_MODULE(data).digest(), byteorder='big')
    hash_from_signature = pow(signature, public_key, n)
    return calculated_hash == hash_from_signature


def validate_hash(hash_object, signature, public_key=None, n=None):
    if public_key is None:
        public_key = registry.get_value(settings.PUBLIC_KEY_REGISTRY)
    if n is None:
        n = registry.get_value(settings.MODULO_REGISTRY)

    calculated_hash = int.from_bytes(hash_object.digest(), byteorder='big')
    hash_from_signature = pow(signature, public_key, n)
    return calculated_hash == hash_from_signature
