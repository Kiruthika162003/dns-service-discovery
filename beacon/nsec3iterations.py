"""NSEC3 iterations: extra hashing meant to slow attackers that in fact taxes the defender more.

NSEC3 hashes zone names before publishing them so that authenticated
denial does not hand out the plaintext names, and it was given an
iteration count, hashing repeatedly, on the theory that more
iterations raise the cost of an offline dictionary attack against
those hashes. The theory sounds right and the arithmetic of who pays
refutes it, which is the correction this module records. One assumes
more iterations means more protection, but the attacker computes the
hashes once, offline, at leisure, while the authoritative server and
every validator recompute them on every single query, forever, so
the iterations tax the defender continuously and the attacker only
once. The defender ends up paying far more than the attacker for a
protection that was marginal to begin with, since a determined
attacker cracks a weak-entropy name at any reasonable iteration
count anyway. RFC 9276 followed the measurement to its conclusion
and recommends an iteration count of zero. The module computes the
per-query cost as a function of the iteration count, names zero as
the recommendation, and flags any positive count as the misconfigured
tax it is, recording the guess that more is safer beside the measured
truth that it is not.
"""

from __future__ import annotations

from beacon.errors import Invalid

RECOMMENDED_ITERATIONS = 0


def per_query_cost(base_cost: int, iterations: int) -> int:
    if iterations < 0:
        raise Invalid("an iteration count is never negative")
    return base_cost * (1 + iterations)


def is_harmful(iterations: int) -> bool:
    return iterations > RECOMMENDED_ITERATIONS


def defender_pays_more(iterations: int, queries: int) -> str:
    attacker_cost = 1 + iterations
    defender_cost = queries * (1 + iterations)
    return (
        f"attacker hashes once ({attacker_cost} units), the "
        f"defender hashes on every one of {queries} queries "
        f"({defender_cost} units); the guess that more iterations "
        "means more safety is refuted by who pays"
    )
