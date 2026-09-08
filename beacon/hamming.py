"""Hamming(7,4): add three parity bits so any single-bit error can be corrected.

A checksum can tell you that a block is corrupt but not which bit to
fix; retransmission is the usual remedy, but where retransmission is
impossible or expensive the code itself must carry enough redundancy
to repair the damage. The Hamming(7,4) code protects four data bits
with three parity bits arranged so that each parity bit covers a
distinct overlapping subset of positions. When a single bit flips, the
three parity checks fail in a pattern whose binary value is exactly the
position of the flipped bit, so the decoder reads the failure pattern
as an address and inverts that one bit. This module encodes four data
bits into a seven-bit codeword, and decodes a codeword back to the four
data bits while correcting any single-bit error and reporting the
syndrome that located it. The honest limit is the code's distance: it
corrects one error but cannot correct two, and a double-bit error is
silently miscorrected into a third wrong value, which is why the plain
Hamming code is paired with an overall parity bit in settings that must
at least detect double errors. That extended variant is left out here
in favor of the clearer core.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _check_bits(bits: list[int]) -> None:
    for bit in bits:
        if bit not in (0, 1):
            raise Invalid(
                f"the value {bit} is not a bit; every element must be 0 or 1"
            )


def encode(data: list[int]) -> list[int]:
    if len(data) != 4:
        raise Invalid(
            f"expected 4 data bits but received {len(data)}; the Hamming(7,4) "
            "code encodes exactly four bits at a time"
        )
    _check_bits(data)
    d1, d2, d3, d4 = data
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]


def decode(code: list[int]) -> tuple[list[int], int]:
    if len(code) != 7:
        raise Invalid(
            f"expected a 7-bit codeword but received {len(code)}; the "
            "Hamming(7,4) code produces seven bits"
        )
    _check_bits(code)
    c = list(code)
    s1 = c[0] ^ c[2] ^ c[4] ^ c[6]
    s2 = c[1] ^ c[2] ^ c[5] ^ c[6]
    s3 = c[3] ^ c[4] ^ c[5] ^ c[6]
    syndrome = s1 + 2 * s2 + 4 * s3
    if syndrome:
        c[syndrome - 1] ^= 1
    return [c[2], c[4], c[5], c[6]], syndrome
