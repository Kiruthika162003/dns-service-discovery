"""The Sieve of Eratosthenes: find every prime up to a bound by crossing out multiples.

Finding all the primes up to some bound is done far faster by
elimination than by testing each number in turn. The sieve starts
with every number marked prime and walks upward: the first unmarked
number, two, is prime, and all its multiples are crossed out as
composite, then the next still-unmarked number, three, is prime and
its multiples are crossed out, and so on. A number survives to be
declared prime exactly when no smaller prime divided it. The work is
close to linear in the bound because each composite is crossed out by
its prime factors and no more, and the crossing-out can start at the
square of each prime, since smaller multiples were already handled by
smaller primes. The tradeoff the module makes plain is memory: the
sieve holds a mark for every number up to the bound, so it is the
right tool for enumerating all primes in a range but the wrong one
for a single large primality question, where allocating an array up
to that number is impossible and a probabilistic test like
Miller-Rabin answers without enumerating anything. The module returns
the list of primes up to and including the bound, and refuses a
negative bound, below which there are no numbers to sieve.
"""

from __future__ import annotations

from beacon.errors import Invalid


def primes_up_to(bound: int) -> list[int]:
    if bound < 0:
        raise Invalid("the bound is non-negative; below zero there are no numbers")
    if bound < 2:
        return []
    is_prime = [True] * (bound + 1)
    is_prime[0] = is_prime[1] = False
    p = 2
    while p * p <= bound:
        if is_prime[p]:
            for multiple in range(p * p, bound + 1, p):
                is_prime[multiple] = False
        p += 1
    return [n for n in range(2, bound + 1) if is_prime[n]]
