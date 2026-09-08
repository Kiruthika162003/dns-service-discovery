"""Binary GCD: Stein's algorithm, a greatest common divisor without division.

Euclid's algorithm finds a greatest common divisor by repeated
remainder, but the modulo operation is comparatively expensive on
hardware where a divide costs many times what a shift or subtract does.
Stein's algorithm reaches the same answer using only subtraction,
comparison, and division by two, which is a bit shift. It rests on three
facts: the gcd of two even numbers is twice the gcd of their halves, the
gcd of an even and an odd number is unchanged by halving the even one
since two cannot be a common factor, and the gcd of two odd numbers
equals the gcd of their difference, which is even, and the smaller. So
it strips out and remembers the common powers of two, halves away the
factors of two that only one operand has, and reduces the remaining pair
of odd numbers by subtraction until one becomes zero, then shifts the
accumulated twos back in. The honest note is that the practical win is
narrow: on a modern processor with a fast divider and on Python's
arbitrary-precision integers where each shift touches every limb, this
is not faster than Euclid, and the standard library's gcd will beat
both. Its value is as the division-free method itself, the one that fits
where division does not. This module returns the gcd of two
non-negative integers and refuses a negative input.
"""

from __future__ import annotations

from beacon.errors import Invalid


def binary_gcd(a: int, b: int) -> int:
    if a < 0 or b < 0:
        raise Invalid(
            f"cannot take the binary gcd of the negative pair ({a}, {b}); this "
            "form is defined over the non-negative integers"
        )
    if a == 0:
        return b
    if b == 0:
        return a
    shift = 0
    while ((a | b) & 1) == 0:
        a >>= 1
        b >>= 1
        shift += 1
    while (a & 1) == 0:
        a >>= 1
    while b:
        while (b & 1) == 0:
            b >>= 1
        if a > b:
            a, b = b, a
        b -= a
    return a << shift
