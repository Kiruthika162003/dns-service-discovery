"""Space-Saving keeps the dominant name in three counters while a hundred cold names churn past.

The point of Space-Saving is that a genuine heavy hitter survives no
matter how many one-off names stream past its handful of counters,
and the drill puts that under pressure. With only three counters it
sends one name a hundred times and then a hundred distinct cold
names, each of which competes for a slot, and holds that the heavy
name is still tracked with an estimate of at least its true hundred
and still tops the ranking. A summary that let the dominant name be
evicted by the churn would miss exactly the thing it exists to find,
so the drill fixes that the heavy hitter is retained and correctly
ranked against a flood of cold competitors far outnumbering the
counters.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.spacesaving import SpaceSaving


def run() -> Finding:
    summary = SpaceSaving(capacity=3)
    for _ in range(100):
        summary.offer("heavy")
    for i in range(100):
        summary.offer(f"cold-{i}")
    estimate = summary.estimate("heavy")
    top = summary.top(1)
    numbers = {
        "heavy_estimate": estimate,
        "at_least_truth": estimate >= 100,
        "top_name": top[0][0] if top else None,
        "heavy_is_top": bool(top) and top[0][0] == "heavy",
    }
    holds = estimate >= 100 and bool(top) and top[0][0] == "heavy"
    return Finding(
        drill="heavyhitter",
        claim=(
            "with three counters a name seen 100 times survives 100 "
            "cold competitors, estimating at least 100 and topping "
            "the ranking, so the heavy hitter is never churned out"
        ),
        numbers=numbers,
        holds=holds,
    )
