
import construct
import enum
import zlib

import settings


class MessageType(enum.IntEnum):
    VERSION_UPDATE = 1
    SERVER_UPDATE = 2
    REQUEST_UPDATE = 3


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

REQUEST_UPDATE_MESSAGE =    construct.FixedSized(settings.MESSAGE_SIZE,
                                construct.Struct(
                                    "type"              / construct.Const(MessageType.REQUEST_UPDATE.value, construct.Byte),
                                    "crc32"             / construct.Int32ub,
                                    "listening_port"    / construct.Int16ub,
                                    "major"             / construct.Int16ub,
                                    "minor"             / construct.Int16ub,
                                ))


def calculate_crc(message):
    m = GENERIC_MESSAGE.parse(message)
    return zlib.crc32(m.data)
