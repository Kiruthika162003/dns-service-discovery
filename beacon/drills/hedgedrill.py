"""Hedging's counterintuitive arithmetic: a fraction of the load buys most of the tail.

The instinct that a hedge doubles load is the thing this drill
exists to refute with numbers. Over a latency sample that is fast
ninety-five times and slow five, a hedge set at the boundary
fires on exactly the slow five percent, so the extra load is a
twentieth, not a double, and the slow request's latency collapses
from five hundred to the delay plus a fast backup. The drill holds
both the small load and the large tail improvement together,
because either alone would mislead: a cheap hedge that did not
help the tail would be pointless, and a hedge that helped the tail
by doubling every request would be the expensive mistake people
fear it is.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.hedging import Hedge

LATENCIES = [10] * 95 + [500] * 5


def run() -> Finding:
    hedge = Hedge(hedge_after_ms=100)
    fraction = hedge.extra_load_fraction(LATENCIES)
    tail_before = max(LATENCIES)
    tail_after = hedge.effective_ms(500, 25)
    numbers = {
        "extra_load_fraction": fraction,
        "tail_before": tail_before,
        "tail_after": tail_after,
        "load_is_small": fraction <= 0.05,
        "tail_collapsed": tail_after < tail_before,
    }
    holds = (
        fraction == 0.05
        and tail_after == 125
        and tail_after < tail_before
    )
    return Finding(
        drill="hedge",
        claim=(
            "a p95 hedge fires on 5% of requests, not double, and "
            "collapses the slow tail from 500ms to 125ms, so a "
            "twentieth of the load buys most of the tail"
        ),
        numbers=numbers,
        holds=holds,
    )
