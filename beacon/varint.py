"""Varint encoding: spend one byte on small numbers, more only as the number grows.

Many numbers in a protocol are small most of the time, a record
length, a count, a field number, and spending a fixed four or eight
bytes on each wastes space when the common value fits in one. A
variable-length integer encodes seven bits of the number per byte and
uses the eighth, the high bit, as a continuation flag: set means more
bytes follow, clear means this is the last. So a number under 128
takes one byte, under 16384 two, and so on, and a stream of mostly
small values is compact. The cost the module keeps honest is the
flip side of the variable width. You cannot index into a sequence of
varints without decoding from the start, since a value's size is not
known until its terminating byte is read, and a truncated stream is
ambiguous, a dangling continuation bit promising a byte that never
arrives, which the decoder must reject rather than guess. The module
encodes a non-negative integer to its minimal byte sequence, decodes
one from the front of a byte string returning the value and how many
bytes it consumed, and refuses a negative input, which has no
unsigned varint form, and a truncated sequence whose final byte still
sets the continuation bit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def encode(value: int) -> bytes:
    if value < 0:
        raise Invalid(
            "a negative integer has no unsigned varint form; use a "
            "zigzag mapping first if signed values are needed"
        )
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def decode(data: bytes) -> tuple[int, int]:
    value = 0
    shift = 0
    for index, byte in enumerate(data):
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index + 1
        shift += 7
    raise Invalid(
        "the varint is truncated: the final byte still sets the "
        "continuation bit, promising a byte that never arrived"
    )
