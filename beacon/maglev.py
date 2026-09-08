"""Maglev hashing: a lookup table built so load is even and a change barely stirs it.

Maglev builds a fixed lookup table whose slots each name a
backend, and a key is served by hashing it into a slot. The
table is filled by a permutation game: every backend proposes
slots in an order derived from two hashes, an offset and a
coprime skip, and the backends take turns claiming their most
preferred still-empty slot until the table is full. Two
properties fall out and both matter for service discovery. Load
is even, because the round-robin turns hand every backend
roughly the same number of slots, and disruption is small,
because when a backend leaves only its slots need new owners and
the permutation hands most of the others back to who held them.
The table size must be prime and comfortably larger than the
backend count, since the coprime skip relies on the primality to
visit every slot, and a table barely larger than the pool would
leave a backend starved. The module measures the evenness and
the disruption rather than asserting them, because both are
claims a build can quietly break.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def _hash(data: str, seed: int) -> int:
    digest = hashlib.blake2b(
        f"{seed}:{data}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big")


class MaglevTable:
    def __init__(self, backends: list[str], size: int = 97) -> None:
        if not backends:
            raise Invalid("a Maglev table needs at least one backend")
        if not _is_prime(size):
            raise Invalid(
                f"the table size {size} is not prime; the coprime "
                "skip depends on primality to reach every slot"
            )
        if size <= len(backends):
            raise Invalid(
                f"a table of {size} slots barely larger than "
                f"{len(backends)} backends would starve one; make "
                "the table comfortably larger than the pool"
            )
        self.backends = list(backends)
        self.size = size
        self.entry = self._build()

    def _permutation(self, backend: str) -> tuple[int, int]:
        offset = _hash(backend, 1) % self.size
        skip = _hash(backend, 2) % (self.size - 1) + 1
        return offset, skip

    def _build(self) -> list[int]:
        count = len(self.backends)
        offsets_skips = [
            self._permutation(b) for b in self.backends
        ]
        nexts = [0] * count
        entry = [-1] * self.size
        filled = 0
        while True:
            for index in range(count):
                offset, skip = offsets_skips[index]
                candidate = (offset + nexts[index] * skip) % self.size
                while entry[candidate] >= 0:
                    nexts[index] += 1
                    candidate = (
                        offset + nexts[index] * skip
                    ) % self.size
                entry[candidate] = index
                nexts[index] += 1
                filled += 1
                if filled == self.size:
                    return entry

    def lookup(self, key: str) -> str:
        slot = _hash(key, 0) % self.size
        return self.backends[self.entry[slot]]

    def load(self) -> dict[str, int]:
        counts = dict.fromkeys(self.backends, 0)
        for index in self.entry:
            counts[self.backends[index]] += 1
        return counts

    def spread(self) -> int:
        counts = self.load().values()
        return max(counts) - min(counts)


def disruption(before: MaglevTable, after: MaglevTable, keys: list[str]) -> float:
    moved = sum(
        1 for key in keys if before.lookup(key) != after.lookup(key)
    )
    return moved / len(keys)
