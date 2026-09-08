"""A counting Bloom filter: gain deletion by replacing bits with counters, and pay for it.

A plain Bloom filter cannot delete: clearing an item's bits might
clear a bit another item also set, creating a false negative, so once
added a key stays forever. A counting Bloom filter buys deletion by
replacing each bit with a small counter. Adding an item increments
the counters at its hash positions, removing it decrements them, and
membership holds only if all its positions are still above zero, so
an item's removal lowers the counters it raised without disturbing
those another item independently raised. The cost is twofold and the
module keeps both in view. Memory multiplies, since a counter of
several bits replaces each single bit, so a counting filter is a few
times larger for the same capacity. And deletion introduces a hazard
the plain filter never had: removing an item that was never added
decrements counters it did not raise, which can drop a shared counter
to zero and produce a false negative for an item that really is
present, so removes must be paired with genuine prior adds. The
module increments and decrements the counters, tests membership as
all-positive, and refuses a remove that would underflow a counter,
since that is the corruption the pairing rule exists to prevent.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


class CountingBloom:
    def __init__(self, size: int, num_hashes: int) -> None:
        if size < 1 or num_hashes < 1:
            raise Invalid("a counting filter needs positive size and hashes")
        self.size = size
        self.num_hashes = num_hashes
        self.counts = [0] * size

    def _positions(self, item: str) -> list[int]:
        positions = []
        for seed in range(self.num_hashes):
            digest = hashlib.blake2b(
                f"{seed}:{item}".encode(), digest_size=8
            ).digest()
            positions.append(int.from_bytes(digest, "big") % self.size)
        return positions

    def add(self, item: str) -> None:
        for position in self._positions(item):
            self.counts[position] += 1

    def remove(self, item: str) -> None:
        positions = self._positions(item)
        if any(self.counts[p] == 0 for p in positions):
            raise Invalid(
                "removing an item whose counters are not all set would "
                "underflow and create a false negative; removes must "
                "pair with prior adds"
            )
        for position in positions:
            self.counts[position] -= 1

    def contains(self, item: str) -> bool:
        return all(self.counts[p] > 0 for p in self._positions(item))
