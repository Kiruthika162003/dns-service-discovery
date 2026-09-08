"""Zigzag encoding: map signed integers to unsigned so small magnitudes stay small.

A varint encodes small non-negative integers in few bytes, but signed
values break it, because a small negative number like minus one, in
two's complement, has all its high bits set and looks enormous to a
varint, taking the maximum number of bytes for the smallest magnitude.
Zigzag encoding fixes it by reordering the integers so that small
magnitudes of either sign map to small non-negative codes. It
interleaves the signs: zero maps to zero, minus one to one, one to
two, minus two to three, and so on, so a value's code grows with its
absolute value rather than with its sign, and the reordered code then
varint-encodes to few bytes exactly when the original was small in
magnitude. The mapping is a bijection, so decoding recovers the exact
signed value, and the whole point is to be the companion of varint
encoding for signed fields, which is where protocol buffers and
similar formats use it. The module encodes a signed integer to its
non-negative zigzag code and decodes a code back to the signed
integer, the two exact inverses, so a signed value can ride a varint
as cheaply as an unsigned one of the same magnitude.
"""

from __future__ import annotations

from beacon.errors import Invalid


def encode(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def decode(code: int) -> int:
    if code < 0:
        raise Invalid("a zigzag code is a non-negative integer")
    return code // 2 if code % 2 == 0 else -(code + 1) // 2
