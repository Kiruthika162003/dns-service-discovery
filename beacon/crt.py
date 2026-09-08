"""Chinese Remainder Theorem: stitch many small congruences into one large one.

When a value is known only through its remainders against several
moduli, the Chinese Remainder Theorem reconstructs the single value
modulo their product, provided the moduli are pairwise coprime. The
appeal is not the trick itself but what it buys: arithmetic on one
awkward large modulus can be carried out in parallel on several small
ones and reassembled at the end, which is how big-integer libraries
and some cryptographic schemes stay fast. This module solves the
classic form. For each congruence it takes the product of all the
other moduli, finds that product's inverse against this modulus, and
weights the remainder by the two so that the term is correct against
its own modulus and vanishes against every other. The honest limit is
the coprimality requirement: if two moduli share a factor the system
may still be consistent, but this construction does not apply and the
module refuses rather than returning a plausible wrong answer, because
a silent wrong reconstruction is worse than a clear refusal. It
verifies pairwise coprimality up front and reports the first offending
pair by name.
"""

from __future__ import annotations

from math import gcd

from beacon.errors import Invalid


def _extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x, y = _extended_gcd(b, a % b)
    return g, y, x - (a // b) * y


def solve(remainders: list[int], moduli: list[int]) -> int:
    if len(remainders) != len(moduli):
        raise Invalid(
            f"there are {len(remainders)} remainders but {len(moduli)} "
            "moduli; each remainder needs exactly one modulus"
        )
    if not moduli:
        raise Invalid("no congruences were given; there is nothing to solve")
    for index, modulus in enumerate(moduli):
        if modulus <= 0:
            raise Invalid(
                f"modulus at position {index} is {modulus}; every modulus "
                "must be a positive integer"
            )
    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            if gcd(moduli[i], moduli[j]) != 1:
                raise Invalid(
                    f"moduli {moduli[i]} and {moduli[j]} share a factor; the "
                    "Chinese Remainder Theorem needs pairwise coprime moduli"
                )
    product = 1
    for modulus in moduli:
        product *= modulus
    total = 0
    for remainder, modulus in zip(remainders, moduli, strict=True):
        partial = product // modulus
        _, inverse, _ = _extended_gcd(partial, modulus)
        total += remainder * partial * inverse
    return total % product
