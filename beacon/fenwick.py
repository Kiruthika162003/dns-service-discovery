"""A Fenwick tree: point updates and prefix sums both in logarithmic time.

Keeping a live count that supports two operations at once, adding to
one position and asking for the sum of a range, is awkward with a
plain array, which does one in constant time and the other in linear.
A Fenwick tree, or binary indexed tree, does both in logarithmic
time by storing partial sums over cleverly chosen ranges keyed to the
binary representation of the index. An update walks upward, adding
the delta to each partial sum that covers the position, following the
lowest set bit, and a prefix-sum query walks downward, accumulating
the partial sums that tile the range from the start, again by the
lowest set bit, so both touch only a logarithmic number of cells.
That makes it the structure for a statistic that is both updated and
queried constantly, a sliding request-count histogram, a rank over a
changing multiset, where recomputing a sum from scratch on every
query or rebuilding on every update would dominate. The module
implements the point update and the prefix sum with the lowest-set-bit
walk, derives a range sum as the difference of two prefixes, and uses
one-based indexing as the algorithm requires, refusing an index
outside the tree.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Fenwick:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise Invalid("a Fenwick tree needs at least one slot")
        self.size = size
        self.tree = [0] * (size + 1)

    def update(self, index: int, delta: int) -> None:
        if not 1 <= index <= self.size:
            raise Invalid(
                f"index {index} is outside 1..{self.size}; the tree "
                "is one-based"
            )
        while index <= self.size:
            self.tree[index] += delta
            index += index & -index

    def prefix_sum(self, index: int) -> int:
        if not 0 <= index <= self.size:
            raise Invalid(f"index {index} is outside 0..{self.size}")
        total = 0
        while index > 0:
            total += self.tree[index]
            index -= index & -index
        return total

    def range_sum(self, lo: int, hi: int) -> int:
        if lo > hi:
            raise Invalid("the range low must not exceed the high")
        return self.prefix_sum(hi) - self.prefix_sum(lo - 1)
