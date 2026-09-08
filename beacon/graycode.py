"""Gray code: order the integers so each step flips exactly one bit.

Ordinary binary counting can flip many bits at once. Going from 3 to 4
turns over three bits at the same instant, and any hardware that reads
the bits mid-transition can momentarily see a value that is neither 3
nor 4. Gray code removes that hazard by reordering the codes so that
consecutive values differ in exactly one bit position, which is why it
appears in rotary encoders, Karnaugh maps, and any place where a
sampled counter must never glitch to a wildly wrong reading. The
encoding is deceptively cheap: a value exclusive-ored with itself
shifted right by one gives its Gray code, and the inverse is a running
exclusive-or of the code's bits from the top down. This module encodes
an integer to its Gray code and decodes it back. The honest caveat is
that the single-bit-change property holds along the counting sequence,
not between two arbitrary values, so Gray code protects a counter that
advances by one at a time and offers nothing to a value that can jump.
It refuses a negative input, since the transform is defined here over
the non-negative integers.
"""

from __future__ import annotations

from beacon.errors import Invalid


def to_gray(value: int) -> int:
    if value < 0:
        raise Invalid(
            f"cannot Gray-encode the negative value {value}; the transform is "
            "defined here over the non-negative integers"
        )
    return value ^ (value >> 1)


def from_gray(code: int) -> int:
    if code < 0:
        raise Invalid(
            f"cannot Gray-decode the negative value {code}; a Gray code is a "
            "non-negative bit pattern"
        )
    value = 0
    while code:
        value ^= code
        code >>= 1
    return value
