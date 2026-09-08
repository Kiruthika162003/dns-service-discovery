"""A Bloom filter: it may say maybe-present in error, but never absent when present.

A Bloom filter answers set membership in a fixed amount of memory
that does not grow with the set, and it does so with a one-sided
error that is exactly the right shape for the job it is usually
given. Adding an item sets several bits chosen by hashing it, and a
membership test reports present only if every one of those bits is
already set. Because adding an item only ever sets bits and never
clears them, a test for an item that was truly added always finds
its bits set, so there are no false negatives: if the filter says
absent, the item is absent, with certainty. The error runs the
other way, a false positive, when a different item's bits happen to
have set all the positions a never-added item hashes to, so the
filter may say maybe-present for something it never saw. That
one-sidedness is what makes it ideal for a negative cache, which
asks have I definitely never seen this name, since a false positive
merely costs an unnecessary real lookup while a false negative,
which cannot happen, would wrongly claim a name is unknown. The
module hashes an item to several positions in a bit array, sets and
tests them, and computes the false-positive rate from the load, so
the memory-for-accuracy trade is a number rather than a hope.
"""

from __future__ import annotations

import hashlib
import math

from beacon.errors import Invalid


class BloomFilter:
    def __init__(self, size: int, num_hashes: int) -> None:
        if size < 1:
            raise Invalid("a bit array of zero size stores nothing")
        if num_hashes < 1:
            raise Invalid(
                "a filter with no hash functions sets no bits and "
                "matches everything"
            )
        self.size = size
        self.num_hashes = num_hashes
        self.bits = 0
        self.added = 0

    def _positions(self, item: str) -> list[int]:
        positions = []
        for seed in range(self.num_hashes):
            digest = hashlib.blake2b(
                f"{seed}:{item}".encode(), digest_size=8
            ).digest()
            positions.append(
                int.from_bytes(digest, "big") % self.size
            )
        return positions

    def add(self, item: str) -> None:
        for position in self._positions(item):
            self.bits |= 1 << position
        self.added += 1

    def contains(self, item: str) -> bool:
        return all(
            (self.bits >> position) & 1
            for position in self._positions(item)
        )

    def false_positive_rate(self) -> float:
        exponent = -self.num_hashes * self.added / self.size
        return (1 - math.exp(exponent)) ** self.num_hashes
