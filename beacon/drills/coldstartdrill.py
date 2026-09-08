"""The cold-start burst, measured against the mitigations that tame it.

A resolver holding a thousand hot names restarts and misses
every one upstream at once: a thousand-query burst against an
authority sized for the fifty-query warm steady state, which
the drill confirms overwhelms a three-hundred capacity. The
measurement that matters is that the two mitigations land on
different axes: staggering the restart into five waves drops
the peak to two hundred, under capacity, at the cost of
recovery time, while persistence skips the burst entirely at
the cost of possibly-stale entries bounded by their TTL. The
drill holds both numbers because the operator's instinct, the
fastest possible restart, is exactly the one that fires the
full burst, and a mitigation that trades recovery time for a
survivable authority is the trade the numbers endorse and the
instinct resists.
"""

from __future__ import annotations

from beacon.coldstart import ColdStartModel, reloadable
from beacon.drills.finding import Finding


def run() -> Finding:
    model = ColdStartModel(
        working_set=1000,
        warm_miss_rate=0.05,
        authority_capacity=300,
    )
    staggered = model.staggered_peak(5)
    numbers = {
        "cold_burst": model.cold_burst(),
        "warm_load": model.warm_load(),
        "capacity": 300,
        "naive_overwhelms": model.cold_overwhelms(),
        "staggered_peak": staggered,
        "staggered_survives": staggered <= 300,
        "fresh_reloads": reloadable(10, 30),
        "stale_refused": not reloadable(40, 30),
    }
    holds = (
        numbers["cold_burst"] == 1000
        and numbers["warm_load"] == 50
        and numbers["naive_overwhelms"]
        and numbers["staggered_peak"] == 200
        and numbers["staggered_survives"]
        and numbers["fresh_reloads"]
        and numbers["stale_refused"]
    )
    return Finding(
        drill="coldstart",
        claim=(
            "the naive restart fires a 1000-query burst that "
            "overwhelms a 300 capacity, staggering into five "
            "waves drops the peak to a survivable 200, and "
            "persistence reloads fresh entries while refusing "
            "stale ones, so the fastest restart is the "
            "dangerous one"
        ),
        numbers=numbers,
        holds=holds,
    )
