"""Fast modular exponentiation: base to the exponent modulo m, without forming the giant power.

Raising a number to a large exponent modulo m is the workhorse of
Diffie-Hellman key exchange and RSA, and doing it naively, multiplying
the base by itself the exponent's many times, is hopeless twice over:
the number of multiplications is the exponent itself, astronomically
large, and the intermediate base-to-the-exponent before the modulus
would be a number too big to store. Square-and-multiply fixes both.
It reads the exponent's binary digits and maintains a running result,
squaring the base at each bit and multiplying it into the result only
where the bit is set, so the number of multiplications is the number
of bits in the exponent, logarithmic rather than linear, and it takes
the modulus after every operation so no value ever grows past the
modulus, keeping the arithmetic small. The exact same value comes out
as the naive computation would, only reachable. This logarithmic cost
is what makes public-key cryptography practical, since the exponents
there are hundreds of bits. The module computes base to the exponent
modulo m by square-and-multiply, refusing a non-positive modulus,
which has no residues, and a negative exponent, which would need a
modular inverse rather than repeated squaring.
"""

from __future__ import annotations

from beacon.errors import Invalid


def mod_exp(base: int, exponent: int, modulus: int) -> int:
    if modulus <= 0:
        raise Invalid("the modulus must be positive to have residues")
    if exponent < 0:
        raise Invalid(
            "a negative exponent needs a modular inverse, not repeated "
            "squaring; this computes non-negative powers"
        )
    result = 1 % modulus
    base %= modulus
    while exponent:
        if exponent & 1:
            result = (result * base) % modulus
        base = (base * base) % modulus
        exponent >>= 1
    return result
