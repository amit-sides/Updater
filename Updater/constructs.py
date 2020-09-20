
import construct
import enum
import zlib

import settings
import rsa_signing


class MessageType(enum.IntEnum):
    VERSION_UPDATE = 1   # Announces a new version
    SERVER_UPDATE = 2    # Announces a new server information
    REQUEST_VERSION = 3  # Request specific version
    REQUEST_UPDATE = 4   # Request the most updated version


GENERIC_MESSAGE =           construct.FixedSized(settings.MESSAGE_SIZE,
                                construct.Struct(
                                    "type"      / construct.Enum(construct.Byte, MessageType),
                                    "signature" / construct.BytesInteger(settings.SIGNATURE_SIZE),
                                    "data"      / construct.Bytes(settings.MESSAGE_SIZE - settings.SIGNATURE_SIZE - construct.Byte.sizeof())
                                ))

VERSION_UPDATE_MESSAGE =    construct.FixedSized(settings.MESSAGE_SIZE,
                                construct.Struct(
                                    "type"              / construct.Const(MessageType.VERSION_UPDATE.value, construct.Byte),
                                    "header_signature"  / construct.BytesInteger(settings.SIGNATURE_SIZE),
                                    "major"             / construct.Int16ub,
                                    "minor"             / construct.Int16ub,
                                    "size"              / construct.Int32ub,
                                    "update_signature"  / construct.BytesInteger(settings.SIGNATURE_SIZE),
                                    "spread"            / construct.Flag
                                ))

SERVER_UPDATE_MESSAGE =     construct.FixedSized(settings.MESSAGE_SIZE,
                                construct.Struct(
                                    "type"          / construct.Const(MessageType.SERVER_UPDATE.value, construct.Byte),
                                    "signature"     / construct.BytesInteger(settings.SIGNATURE_SIZE),
                                    "address_id"    / construct.Int16ub,    # A running count of the message.
                                                                            # Higher id count means more updated information.
                                                                            # prevents attackers from remotely
                                                                            # 'updating' to old addresses
                                    "address_size"  / construct.Int8ub,
                                    "address"       / construct.Bytes(lambda ctx: ctx.address_size),   # could be a domain or IP
                                    "port"          / construct.Int16ub,
                                    "spread"        / construct.Flag
                                ))

REQUEST_VERSION_MESSAGE =    construct.FixedSized(settings.MESSAGE_SIZE,
                                construct.Struct(
                                    "type"              / construct.Const(MessageType.REQUEST_VERSION.value, construct.Byte),
                                    "crc32"             / construct.Int32ub,
                                    "listening_port"    / construct.Int16ub,
                                    "major"             / construct.Int16ub,
                                    "minor"             / construct.Int16ub,
                                ))

REQUEST_UPDATE_MESSAGE =    construct.FixedSized(settings.MESSAGE_SIZE,
                                construct.Struct(
                                    "type"              / construct.Const(MessageType.REQUEST_UPDATE.value, construct.Byte),
                                    "crc32"             / construct.Int32ub,
                                ))


def calculate_crc(message):
    m = GENERIC_MESSAGE.parse(message)
    return zlib.crc32(m.data)


def sign_message(message):
    m = GENERIC_MESSAGE.parse(message)
    return rsa_signing.sign(m.data)
