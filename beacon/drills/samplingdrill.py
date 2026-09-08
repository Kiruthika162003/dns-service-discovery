"""Reservoir sampling fills, then replaces at a probability that falls as the stream grows.

Reservoir sampling's uniformity rests on the replacement probability
being exactly k over the running count, and the drill checks the
mechanics that guarantee makes concrete rather than the statistics.
It fills a reservoir of three, confirms the first three items are
kept outright, then offers a fourth with a draw at the bottom of the
range and holds that it replaces an early slot, and a fifth with a
draw near the top and holds that the reservoir is left untouched.
Together these fix that entry is certain while the reservoir has
room and that beyond it a replacement lands only when the draw falls
inside the shrinking window, which is the behavior that makes every
item equally likely without knowing the stream's length.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.reservoir import Reservoir


def run() -> Finding:
    res = Reservoir(capacity=3)
    for item in ("a", "b", "c"):
        res.offer(item, draw=0.0)
    filled = res.contents() == ["a", "b", "c"]
    res.offer("d", draw=0.0)
    replaced_early = res.contents()[0] == "d"
    res.offer("e", draw=0.99)
    kept = "e" not in res.contents()
    numbers = {
        "filled_first_three": filled,
        "low_draw_replaced": replaced_early,
        "high_draw_kept": kept,
        "seen": res.seen,
    }
    holds = filled and replaced_early and kept and res.seen == 5
    return Finding(
        drill="reservoir",
        claim=(
            "a reservoir of three fills with the first three, a "
            "low draw on the fourth replaces an early slot, and a "
            "high draw on the fifth leaves it untouched, the "
            "mechanics behind uniform one-pass sampling"
        ),
        numbers=numbers,
        holds=holds,
    )
