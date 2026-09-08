"""A bucketed histogram: latency percentiles in fixed memory, known only to bucket resolution.

Reporting the p99 latency of a service exactly would mean keeping
every sample and sorting them, memory that grows without bound as
traffic does. A histogram trades that exactness for a fixed size by
sorting samples into predefined buckets as they arrive: each
observation increments the counter for the bucket its value falls
in, and nothing else is stored, so memory is the number of buckets
regardless of how many samples pass through. A quantile is then
estimated by walking the buckets, accumulating counts until the
running total crosses the desired rank, and reporting that bucket's
upper bound. The estimate is honest about its limit, it is known
only to bucket resolution, so a p99 lands within the width of a
bucket rather than at an exact value, and the way to make it
sharper is finer buckets, which is more memory, the trade laid bare.
Bucket boundaries are usually spaced to give fine resolution where
latencies cluster and coarse resolution in the long tail. The module
records observations into buckets, estimates a quantile by rank, and
refuses an out-of-range quantile, since a percentile below zero or
above one names no point in the distribution.
"""

from __future__ import annotations

from bisect import bisect_left

from beacon.errors import Invalid


class Histogram:
    def __init__(self, bounds: list[float]) -> None:
        if not bounds or list(bounds) != sorted(bounds):
            raise Invalid(
                "the bucket bounds must be a non-empty ascending "
                "list; unordered bounds place samples in the wrong "
                "bucket"
            )
        self.bounds = list(bounds)
        self.buckets = [0] * (len(bounds) + 1)
        self.total = 0

    def observe(self, value: float) -> None:
        index = bisect_left(self.bounds, value)
        self.buckets[index] += 1
        self.total += 1

    def quantile(self, q: float) -> float:
        if not 0.0 <= q <= 1.0:
            raise Invalid(
                f"a quantile of {q} names no point in the "
                "distribution; it must be between zero and one"
            )
        if self.total == 0:
            raise Invalid("an empty histogram has no quantile to report")
        rank = q * self.total
        running = 0
        for index, count in enumerate(self.buckets):
            running += count
            if running >= rank:
                if index < len(self.bounds):
                    return self.bounds[index]
                return float("inf")
        return float("inf")
