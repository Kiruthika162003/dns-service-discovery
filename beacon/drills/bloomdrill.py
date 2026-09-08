"""The Bloom filter's load-bearing promise: it never denies a member it was given.

A Bloom filter is only safe as a negative cache because of a
guarantee that must actually hold, not merely be claimed: every
item added tests present, always, with no exception. The drill adds
a thousand names and then checks that all thousand are found, since
a single false negative would mean the filter forgot something it
was told, which for a negative cache would be a wrong answer of
absence rather than a harmless extra lookup. It also records that
the false-positive rate rises with load, the other half of the
trade, so the guarantee and its price are held together: no false
negatives ever, and a false-positive rate that grows as the filter
fills, which is the honest shape of the structure.
"""

from __future__ import annotations

from beacon.bloomfilter import BloomFilter
from beacon.drills.finding import Finding


def run() -> Finding:
    bloom = BloomFilter(size=8192, num_hashes=5)
    for i in range(1000):
        bloom.add(f"name-{i}")
    all_found = all(bloom.contains(f"name-{i}") for i in range(1000))
    rate = bloom.false_positive_rate()
    numbers = {
        "added": 1000,
        "all_found": all_found,
        "false_positive_rate": round(rate, 4),
        "rate_is_positive_under_load": rate > 0,
    }
    holds = all_found and rate > 0
    return Finding(
        drill="bloom",
        claim=(
            "all 1000 added names test present, no false negatives, "
            "while the false-positive rate is positive under load, "
            "the exact one-sided error a negative cache needs"
        ),
        numbers=numbers,
        holds=holds,
    )
