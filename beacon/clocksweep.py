"""CLOCK eviction: a cheap near-LRU that gives each touched entry one sweep of grace.

True LRU has to reorder a list on every single access to remember
the exact recency order, which is more bookkeeping than a hot cache
wants to pay. CLOCK approximates it with one reference bit per entry
and a hand that sweeps a circular buffer. Accessing an entry just
sets its reference bit, cheap and lock-light, no reordering. To
evict, the hand advances around the ring: if the entry under the
hand has its reference bit set, the hand clears the bit and moves on,
giving that entry a second chance because it was touched since the
last sweep, and if the bit is already clear the entry is evicted.
The effect is close to least-recently-used, an entry touched
recently survives the next sweep, an entry untouched for a full
revolution is evicted, but at a fraction of the cost, which is why
operating-system page caches use it. The approximation is the honest
cost: an entry touched even once gets a whole sweep of grace, so
CLOCK can keep an entry slightly longer than strict LRU would, and
it evicts in ring order among the unreferenced rather than by exact
recency. The module accesses entries by setting bits, and evicts by
sweeping the hand, clearing bits until it finds one to drop.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Clock:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a cache of zero capacity holds nothing")
        self.capacity = capacity
        self.frames: list[str] = []
        self.ref: dict[str, bool] = {}
        self.hand = 0
        self.last_evicted: str | None = None

    def access(self, key: str) -> None:
        if key in self.ref:
            self.ref[key] = True
            return
        if len(self.frames) < self.capacity:
            self.frames.append(key)
            self.ref[key] = True
            return
        self._evict()
        self.frames.append(key)
        self.ref[key] = True

    def _evict(self) -> None:
        while True:
            self.hand %= len(self.frames)
            candidate = self.frames[self.hand]
            if self.ref[candidate]:
                self.ref[candidate] = False
                self.hand += 1
                continue
            self.frames.pop(self.hand)
            del self.ref[candidate]
            self.last_evicted = candidate
            return

    def resident(self) -> set[str]:
        return set(self.frames)
