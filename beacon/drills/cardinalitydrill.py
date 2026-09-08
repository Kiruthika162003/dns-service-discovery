"""HyperLogLog counts twenty thousand distinct names within a few percent, ignoring duplicates.

The reason to accept an estimate instead of an exact count is that
the estimate is close and the memory is tiny, so the drill checks
both halves of that bargain. It feeds twenty thousand distinct names
and holds that the estimate lands within five percent of the truth,
and it feeds five thousand copies of one name and holds that the
estimate stays near one, proving duplicates do not inflate the
count. A sketch that drifted far on cardinality, or that counted
repeats as new, would break the one thing it promises, so the drill
fixes the accuracy on distinct items and the immunity to duplicates
as the two properties that make the approximation worth taking.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.hyperloglog import HyperLogLog


def run() -> Finding:
    distinct = HyperLogLog(precision=12)
    for i in range(20000):
        distinct.add(f"client-{i}")
    estimate = distinct.estimate()
    error = abs(estimate - 20000) / 20000

    repeats = HyperLogLog(precision=12)
    for _ in range(5000):
        repeats.add("one-client")
    numbers = {
        "true": 20000,
        "estimate": round(estimate),
        "relative_error": round(error, 4),
        "within_5pct": error < 0.05,
        "duplicates_estimate": round(repeats.estimate(), 2),
    }
    holds = error < 0.05 and repeats.estimate() < 5
    return Finding(
        drill="cardinality",
        claim=(
            "HyperLogLog estimates 20000 distinct names within 5% "
            "and counts 5000 copies of one name as under 5, so it "
            "is accurate on distinct items and immune to duplicates"
        ),
        numbers=numbers,
        holds=holds,
    )
