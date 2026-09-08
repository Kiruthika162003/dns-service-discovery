"""Backoff with jitter: spreading retries so a shared failure does not resynchronize them.

Exponential backoff doubles the wait after each failure, which
keeps a struggling server from being hammered, but backoff alone
has a hidden flaw at scale: if a thousand clients all failed at
the same instant, a common outage, they all back off by the same
schedule and retry in the same instant again, and again, a
thundering herd that re-forms on every round and never lets the
server recover. Jitter breaks the synchrony by randomizing the
wait, and the variants differ in how much. Full jitter picks the
wait uniformly between zero and the capped exponential, spreading
the herd across the whole interval; decorrelated jitter, the AWS
refinement, picks between the base and three times the previous
wait, which spreads at least as well while tending to recover
faster after the backoff has grown large. The module computes the
capped exponential and both jittered waits from a supplied random
draw, so the schedules are deterministic to test, and it makes the
point that the no-jitter schedule is the one that resynchronizes
the herd it was meant to disperse.
"""

from __future__ import annotations

from beacon.errors import Invalid


def capped_exponential(base: float, attempt: int, cap: float) -> float:
    if base <= 0:
        raise Invalid("the base wait must be positive")
    if attempt < 0:
        raise Invalid("the attempt count cannot be negative")
    return min(cap, base * (2**attempt))


def full_jitter(
    base: float, attempt: int, cap: float, draw: float
) -> float:
    if not 0.0 <= draw < 1.0:
        raise Invalid(
            f"the random draw {draw} must be in [0, 1); it scales "
            "the interval, it is not the interval"
        )
    ceiling = capped_exponential(base, attempt, cap)
    return draw * ceiling


def decorrelated_jitter(
    base: float, previous: float, cap: float, draw: float
) -> float:
    if not 0.0 <= draw < 1.0:
        raise Invalid("the random draw must be in [0, 1)")
    if previous < base:
        raise Invalid(
            "the previous wait cannot be below the base; the first "
            "decorrelated step starts from the base itself"
        )
    span = previous * 3 - base
    return min(cap, base + draw * span)
