"""Miller-Rabin: decide primality by cross-examining a number, deterministic below a huge bound.

Testing whether a large number is prime by trial division is
hopeless, so cryptography uses a probabilistic test that a witness
either clears the number or convicts it. Miller-Rabin writes the
number minus one as an odd part times a power of two, then raises a
chosen base to that odd part modulo the number and squares it
repeatedly, watching the sequence: a genuine prime forces the
sequence to pass through one in a specific way, and a composite is
caught, failing that pattern, by at least three-quarters of possible
bases. So a handful of independently chosen bases make a false
positive vanishingly unlikely, and below a known bound a specific
fixed set of small bases is provably deterministic, never wrong at
all. This is exactly how the large primes for keys are found, where
sieving up to the number is impossible and the test answers without
enumerating anything. The module tests a number against a fixed set
of bases that is deterministic for every value it could realistically
be handed, so within that range the answer is certain, not
probabilistic. The module decides primality by the witness loop over
those bases, short-circuiting the small cases and refusing a number
below two, which is neither prime nor composite in the usual sense.
"""

from __future__ import annotations

from beacon.errors import Invalid
from beacon.modexp import mod_exp

_WITNESSES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime(n: int) -> bool:
    if n < 2:
        raise Invalid(
            "primality is asked of an integer two or greater; below "
            "that a number is neither prime nor composite here"
        )
    for small in _WITNESSES:
        if n == small:
            return True
        if n % small == 0:
            return False
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for base in _WITNESSES:
        x = mod_exp(base, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True
