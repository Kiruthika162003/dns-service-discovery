"""Jump hash keeps two promises at once: an even spread and a move of only one key in N.

Jump consistent hash claims both an even distribution and minimal
movement when the bucket count grows, and like Maglev those pull
in opposite enough directions that a drill should hold them
together. Over five thousand keys it checks that eight buckets
each land within twenty percent of the average, and that growing
from eight buckets to nine relocates roughly one key in nine and
no more. A build that spread evenly but reshuffled everything on a
resize, or moved little but piled onto one bucket, would fail one
half while passing the other, so the drill fixes both numbers on
the same keys and the same resize.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.jumphash import jump_hash, moved_fraction

KEYS = [f"key-{i}" for i in range(5000)]


def run() -> Finding:
    counts = [0] * 8
    for key in KEYS:
        counts[jump_hash(key, 8)] += 1
    average = len(KEYS) / 8
    spread_ok = (
        max(counts) < average * 1.2 and min(counts) > average * 0.8
    )
    fraction = moved_fraction(KEYS, 8, 9)
    numbers = {
        "max_bucket": max(counts),
        "min_bucket": min(counts),
        "even": spread_ok,
        "moved_fraction": round(fraction, 3),
        "near_one_in_nine": 0.06 < fraction < 0.16,
    }
    holds = spread_ok and 0.06 < fraction < 0.16
    return Finding(
        drill="jumphash",
        claim=(
            "eight jump-hash buckets each land within 20% of the "
            "average over 5000 keys, and growing to nine buckets "
            "moves about one key in nine, holding even spread and "
            "minimal movement together"
        ),
        numbers=numbers,
        holds=holds,
    )
