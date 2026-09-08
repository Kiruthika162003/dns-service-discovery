"""A prefix-sum array: any range sum in constant time over static data, after one pass to build.

When data does not change but its range sums are queried over and
over, the total requests in an hour window, the load across a span of
shards, a prefix-sum array answers each query in constant time. It
precomputes, once, the cumulative sum up to each position, so the sum
of any range is the cumulative sum at the range's end minus the
cumulative sum at its start, a single subtraction, no matter how wide
the range. The build is one linear pass and the storage is one extra
number per element, and thereafter every range sum is O(1), which is
unbeatable for static data queried many times. The limitation is
precisely that it assumes the data is static: changing one element
would change every cumulative sum after it, forcing a linear rebuild
of the whole suffix, so a workload that updates as well as queries is
better served by a Fenwick tree or a segment tree, which accept a
higher per-query cost in exchange for logarithmic updates. The
module builds the cumulative array from a sequence, answers a
half-open range sum by subtracting two cumulative values, and refuses
a range outside the data, which sums nothing meaningful.
"""

from __future__ import annotations

from beacon.errors import Invalid


class PrefixSum:
    def __init__(self, data: list[int]) -> None:
        self.prefix = [0]
        for value in data:
            self.prefix.append(self.prefix[-1] + value)

    def range_sum(self, lo: int, hi: int) -> int:
        n = len(self.prefix) - 1
        if not 0 <= lo <= hi <= n:
            raise Invalid(
                f"range [{lo}, {hi}) is outside the half-open 0..{n}"
            )
        return self.prefix[hi] - self.prefix[lo]

    def total(self) -> int:
        return self.prefix[-1]
