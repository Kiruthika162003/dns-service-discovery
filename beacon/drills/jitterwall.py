"""The renewal wall, measured falling.

A thousand instances registered in one rollout renew as one
metronome tick, and the drill measures the wall twice: naked,
the registry eats one thousand renewals in a single tick,
and jittered, the worst tick holds twenty-nine, a thirty-four
fold collapse bought with zero coordination, each instance
hashing its own name into its slot. The second claim under
test is stability: hashed jitter must give the same worst
tick on every run because determinism is the difference
between a drizzle and a wall that occasionally re-forms by
bad luck, and the drill runs the schedule twice to hold the
protocol to it. Numbers, not adjectives, because smoothing
is precisely the kind of claim that inflates in retellings.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.heartbeatjitter import RenewalSchedule

FLEET = [f"inst-{number}" for number in range(1000)]


def run() -> Finding:
    schedule = RenewalSchedule(interval=60)
    wall, wall_tick = schedule.peak_load(
        FLEET, horizon=180, jittered=False
    )
    drizzle_first, tick_first = schedule.peak_load(
        FLEET, horizon=180, jittered=True
    )
    drizzle_second, tick_second = schedule.peak_load(
        FLEET, horizon=180, jittered=True
    )
    numbers = {
        "fleet": len(FLEET),
        "wall": wall,
        "wall_tick": wall_tick,
        "drizzle_worst": drizzle_first,
        "collapse_factor": wall // drizzle_first,
        "stable_across_runs": (
            drizzle_first == drizzle_second
            and tick_first == tick_second
        ),
    }
    holds = (
        numbers["wall"] == 1000
        and numbers["drizzle_worst"] == 29
        and numbers["collapse_factor"] == 34
        and numbers["stable_across_runs"]
    )
    return Finding(
        drill="jitterwall",
        claim=(
            "the thousand-renewal wall collapses to a worst "
            "tick of twenty-nine, a thirty-four fold drop "
            "bought with zero coordination, and the drizzle "
            "is stable across runs because hashed slots do "
            "not re-form walls by bad luck"
        ),
        numbers=numbers,
        holds=holds,
    )
