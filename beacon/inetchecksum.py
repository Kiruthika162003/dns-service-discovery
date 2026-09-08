"""The Internet checksum: a cheap one's-complement sum that catches much and misses a little.

The checksum in IP, TCP, and UDP headers is deliberately cheap,
because it runs on every packet: it treats the data as a sequence of
sixteen-bit words, adds them with end-around carry, folding any
overflow back into the low bits, and stores the one's-complement of
that sum. A receiver adds the same words including the stored
checksum and gets all-ones if nothing changed, so verification is the
same cheap addition. Its virtue is speed, only adds and a fold, no
lookup table like a CRC, and it does catch the common single-bit and
many multi-bit corruptions. Its honest weakness, which the module
does not hide, is that being a sum it is blind to errors that leave
the sum unchanged: swapping two words does not change their total, and
certain compensating bit changes cancel, so it misses reorderings and
patterns a cyclic redundancy check would catch. That is why it is the
transport-and-network-layer checksum, fast and good enough given a
stronger link-layer CRC beneath it, rather than a standalone
integrity guarantee. The module computes the checksum over a byte
string, padding an odd length, and verifies that data carrying its
checksum sums to all-ones, refusing nothing since any bytes have a
checksum.
"""

from __future__ import annotations


def _ones_complement_sum(data: bytes) -> int:
    if len(data) % 2:
        data = data + b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return total


def checksum(data: bytes) -> int:
    return (~_ones_complement_sum(data)) & 0xFFFF


def verify(data: bytes, stored_checksum: int) -> bool:
    total = _ones_complement_sum(data) + stored_checksum
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return total == 0xFFFF
