"""CRC-32: catch burst errors a checksum misses, paying shift-and-xor per bit for the strength.

A cyclic redundancy check treats the data as a big polynomial and
takes its remainder modulo a fixed generator polynomial, and that
algebra gives it error-detection guarantees a sum-based checksum
cannot match: it catches every single-bit error, every double-bit
error within its reach, any odd number of bit errors, and every burst
of errors shorter than its width, which is why link and storage
layers use it where corruption must not slip through. The cost is
compute: the bitwise form shifts and conditionally xors the generator
for every bit of the input, more work than Fletcher's two additions
per byte, though a precomputed per-byte table trades memory to speed
it up. So the choice against Fletcher is detection strength versus
speed, and CRC is the pick when an undetected error is expensive. The
module computes the standard CRC-32 with the reversed generator
polynomial and the usual initial and final inversion, reproducing the
value other tools compute so a checksum written by one is verified by
another, and it detects that a corrupted byte changes the result.
"""

from __future__ import annotations

_POLY = 0xEDB88320


def crc32(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ _POLY
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF
