"""Burrows-Wheeler transform: a reversible reordering that clusters like symbols.

The Burrows-Wheeler transform does not compress anything by itself; it
rearranges a block of bytes into a permutation that later stages can
compress far better than the original. It sorts every rotation of the
block and reads off the last column, and the arithmetic of that sort
tends to bring bytes that share a following context next to each other,
so text with repeated words emerges as long runs of the same byte. Those
runs are what a move-to-front stage followed by run-length or entropy
coding feed on, and this pipeline is the heart of bzip2. What makes the
transform remarkable is that it is exactly reversible from the last
column and one integer, the index of the original block among the sorted
rotations, because the first column is just the last column sorted and
the two columns together pin down the cycle that reconstructs the input.
This module transforms a block that ends in a unique sentinel byte and
inverts it. The honest cost is the sort: the direct method here builds
and sorts the rotations outright, which is quadratic in the block size
and clear to read, where a production coder uses a suffix array to reach
linear time at the price of much more intricate code.
"""

from __future__ import annotations

from beacon.errors import Invalid

SENTINEL = 0


def transform(block: bytes) -> tuple[bytes, int]:
    if SENTINEL in block:
        raise Invalid(
            f"the block already contains the sentinel byte {SENTINEL}; the "
            "transform needs a byte that appears nowhere in the input"
        )
    padded = block + bytes([SENTINEL])
    n = len(padded)
    rotations = sorted(padded[i:] + padded[:i] for i in range(n))
    last_column = bytes(rotation[-1] for rotation in rotations)
    original_index = rotations.index(padded)
    return last_column, original_index


def invert(last_column: bytes, original_index: int) -> bytes:
    n = len(last_column)
    if n == 0:
        raise Invalid("the last column is empty; there is nothing to invert")
    if not 0 <= original_index < n:
        raise Invalid(
            f"the original index {original_index} is outside the range "
            f"0 to {n - 1}; it cannot name a rotation of this block"
        )
    table = [b"" for _ in range(n)]
    for _ in range(n):
        table = sorted(
            bytes([last_column[i]]) + table[i] for i in range(n)
        )
    reconstructed = table[original_index]
    return reconstructed[:-1]
