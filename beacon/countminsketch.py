"""Count-min sketch: approximate frequencies that overestimate but never undercount.

Counting how often each of millions of names is queried, to find
the hot ones, would take a counter per name and memory that grows
with the traffic. A count-min sketch trades exactness for a fixed
size. It is a grid of counters, several rows each hashed
independently, and adding an item increments one counter per row at
the position that row hashes it to. Collisions inflate individual
counters, since unrelated items share cells, but the estimate for
an item is the minimum of its counters across the rows, and taking
the minimum is what makes the error one-sided: every counter for an
item is at least its true count, because every occurrence
incremented all of them, so the minimum is also at least the true
count and never below it. The estimate can therefore overshoot, when
every row happened to collide, but it can never undershoot, which is
exactly the guarantee heavy-hitter detection needs, because a truly
frequent name is never hidden by the sketch, only an infrequent one
might be wrongly inflated. The module builds the grid, adds items
across the rows, and estimates a frequency as the row-wise minimum,
so the memory is fixed and the error has a known direction.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


class CountMinSketch:
    def __init__(self, width: int, depth: int) -> None:
        if width < 1 or depth < 1:
            raise Invalid(
                "a sketch needs at least one row and one column to "
                "count into"
            )
        self.width = width
        self.depth = depth
        self.rows = [[0] * width for _ in range(depth)]

    def _column(self, row: int, item: str) -> int:
        digest = hashlib.blake2b(
            f"{row}:{item}".encode(), digest_size=8
        ).digest()
        return int.from_bytes(digest, "big") % self.width

    def add(self, item: str, count: int = 1) -> None:
        if count < 0:
            raise Invalid(
                "a count-min sketch counts occurrences and cannot "
                "decrement; a negative add would break the never-"
                "undercount guarantee"
            )
        for row in range(self.depth):
            self.rows[row][self._column(row, item)] += count

    def estimate(self, item: str) -> int:
        return min(
            self.rows[row][self._column(row, item)]
            for row in range(self.depth)
        )
