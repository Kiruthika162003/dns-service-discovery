"""Quickselect: find the kth smallest, a percentile, in expected linear time without sorting.

Answering what is the p99 latency needs one order statistic, the kth
smallest value, not the whole sorted order, and sorting to get it
wastes work. Quickselect gets it in expected linear time by borrowing
quicksort's partition without its full recursion. It picks a pivot,
partitions the values into those below and above it, and then recurses
into only the one side that must contain the target rank, discarding
the other half each step, so the work halves on average rather than
sorting everything. That gives expected linear time, faster than a
sort when a single percentile is wanted. The honest caveat is the
worst case: a pivot that repeatedly splits off just one element, which
an adversarial or already-sorted input can force with a naive pivot
choice, degrades it to quadratic, and guaranteeing linear time
requires a smarter pivot, median-of-medians, at a higher constant
factor. The module selects the kth smallest by partitioning around a
pivot and recursing into the relevant side, derives a percentile from
a rank, and refuses a rank outside the data, which names no order
statistic.
"""

from __future__ import annotations

from math import ceil

from beacon.errors import Invalid


def kth_smallest(items: list[int], k: int) -> int:
    if not 1 <= k <= len(items):
        raise Invalid(
            f"rank {k} is outside 1..{len(items)}; it names no order "
            "statistic of this data"
        )
    values = list(items)
    target = k - 1
    lo, hi = 0, len(values) - 1
    while lo < hi:
        pivot = values[(lo + hi) // 2]
        i, j = lo, hi
        while i <= j:
            while values[i] < pivot:
                i += 1
            while values[j] > pivot:
                j -= 1
            if i <= j:
                values[i], values[j] = values[j], values[i]
                i += 1
                j -= 1
        if target <= j:
            hi = j
        elif target >= i:
            lo = i
        else:
            break
    return values[target]


def percentile(items: list[int], q: float) -> int:
    if not 0.0 < q <= 1.0:
        raise Invalid("a percentile fraction must be in (0, 1]")
    rank = max(1, ceil(q * len(items)))
    return kth_smallest(items, rank)
