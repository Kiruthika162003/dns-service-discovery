"""Modular inverse: the number that undoes a multiplication mod m, when one exists at all.

Where modular exponentiation is the encrypt side of public-key
arithmetic, the modular inverse is often the decrypt side: the number
that, multiplied by a given one modulo m, yields one, undoing the
multiplication. It does not always exist, and its absence is a fact
about the ring rather than a failure to compute: an inverse of a
modulo m exists precisely when a and m are coprime, because only then
can repeated addition of a reach every residue including one. The
extended Euclidean algorithm finds it in logarithmic time as a side
effect of computing the greatest common divisor: while reducing a and
m it tracks the coefficients of a and m that produce each remainder,
so when the remainder reaches the gcd it has expressed that gcd as a
combination of a and m, and if the gcd is one the coefficient on a is
the inverse. The module runs the extended algorithm, returns the
inverse reduced into the range zero to m, and refuses an input not
coprime to the modulus by reporting that no inverse exists, since
returning a wrong number there would silently corrupt whatever
decryption or division relied on it.
"""

from __future__ import annotations

from beacon.errors import Invalid


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_r, old_s, old_t


def mod_inverse(a: int, m: int) -> int:
    if m <= 0:
        raise Invalid("the modulus must be positive to have residues")
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise Invalid(
            f"{a} has no inverse modulo {m}; they are not coprime, so "
            "no multiplier undoes it, which is a fact about the ring"
        )
    return x % m
