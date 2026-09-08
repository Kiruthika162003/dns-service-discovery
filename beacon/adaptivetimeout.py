"""Adaptive timeout: derive the deadline from the latency distribution, not a fixed guess.

A fixed request timeout is wrong the moment the latency
distribution shifts, and it shifts constantly: a fixed two seconds
that was generous at launch becomes trigger-happy under load when
the honest tail stretches past it, cutting off requests that would
have succeeded, or becomes sluggish when the service speeds up,
waiting seconds to detect a failure that a fast service would have
answered in milliseconds. An adaptive timeout tracks the observed
distribution instead. It sets the deadline from a high percentile
of recent latencies plus a margin, so it sits just above where
healthy requests land and treats anything slower as the failure it
probably is. The tension it must respect is that a timeout set too
close to the tail cuts off the naturally slow but successful
requests that live in that tail, while one set too far above wastes
time detecting real failures, so the margin is the dial between
false timeouts and slow detection. The module computes the timeout
from a high percentile and a margin over a floor, and refuses a
margin below one, since a deadline under the very percentile it is
built on would fail the healthy requests that define it.
"""

from __future__ import annotations

from beacon.errors import Invalid


def percentile(samples: list[float], fraction: float) -> float:
    if not samples:
        raise Invalid("no samples to take a percentile of")
    if not 0.0 <= fraction <= 1.0:
        raise Invalid(
            f"a percentile fraction of {fraction} is not between "
            "zero and one"
        )
    ordered = sorted(samples)
    index = min(
        len(ordered) - 1, int(fraction * (len(ordered) - 1) + 0.5)
    )
    return ordered[index]


def adaptive_timeout(
    samples: list[float],
    fraction: float = 0.99,
    margin: float = 1.5,
    floor: float = 0.0,
) -> float:
    if margin < 1.0:
        raise Invalid(
            "a margin below one puts the deadline under the very "
            "percentile it is built on, failing the healthy "
            "requests that define it"
        )
    tail = percentile(samples, fraction)
    return max(floor, tail * margin)
