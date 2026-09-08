"""A segment tree: range sums and point updates both in logarithmic time, over changing data.

A prefix-sum array answers a range sum in constant time but costs a
linear rebuild on any update, which is useless when the underlying
data changes as often as it is queried. A segment tree keeps both
cheap. It stores the array at the leaves of a binary tree and, at
each internal node, the aggregate of its two children, so an update
changes one leaf and walks up recomputing the log-many ancestors on
its path, and a range query combines the log-many nodes that exactly
tile the queried span. Both operations touch only a logarithmic
number of nodes. The tree generalizes beyond sums to any associative
combination, minimum, maximum, greatest common divisor, by changing
the merge at each node, which is where it goes further than a Fenwick
tree, the lighter structure limited to invertible operations like
sums. The module implements the array-backed iterative form: a point
update that sets a leaf and folds the change upward, and a
half-open range query that walks inward from both ends combining the
boundary nodes. It refuses an index or range outside the array, since
a query beyond the data aggregates nothing meaningful.
"""

from __future__ import annotations

from beacon.errors import Invalid


class SegmentTree:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise Invalid("a segment tree needs at least one leaf")
        self.n = size
        self.tree = [0] * (2 * size)

    def update(self, index: int, value: int) -> None:
        if not 0 <= index < self.n:
            raise Invalid(f"index {index} is outside 0..{self.n - 1}")
        pos = index + self.n
        self.tree[pos] = value
        pos //= 2
        while pos >= 1:
            self.tree[pos] = self.tree[2 * pos] + self.tree[2 * pos + 1]
            pos //= 2

    def range_sum(self, lo: int, hi: int) -> int:
        if not 0 <= lo <= hi <= self.n:
            raise Invalid(
                f"range [{lo}, {hi}) is outside the half-open 0..{self.n}"
            )
        result = 0
        left = lo + self.n
        right = hi + self.n
        while left < right:
            if left & 1:
                result += self.tree[left]
                left += 1
            if right & 1:
                right -= 1
                result += self.tree[right]
            left //= 2
            right //= 2
        return result
