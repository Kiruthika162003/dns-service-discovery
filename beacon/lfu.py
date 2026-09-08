"""An LFU cache: evict the least frequently used, scan-resistant but slow to forget.

Where LRU bets on recency, LFU bets on frequency: the entry hit the
fewest times is the one dropped when the cache fills, on the theory
that a key wanted often will be wanted again. This gives LFU the
property LRU lacks, resistance to a scan, because the one-time keys
of a sweep each accumulate a frequency of one and are evicted before
they can displace a hot key that has been hit many times, so the
working set survives a scan that would have flushed an LRU cache.
The weakness is the mirror of that strength and the module names it:
LFU clings to keys that were popular once and no longer are, since
their high historical count protects them long after the traffic
moved on, so a formerly-hot key can squat in the cache while genuine
newcomers are evicted for having a lower count they never had a
chance to build. That is cache pollution by stale favorites, the
reason real LFU caches add decay or aging, and the module implements
the core policy, evicting the minimum frequency and breaking ties by
which of the least-frequent was least recently inserted, so the
behavior and its blind spot are both visible.
"""

from __future__ import annotations

from beacon.errors import Invalid


class LFUCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a cache of zero capacity is a miss on every lookup")
        self.capacity = capacity
        self.values: dict[str, str] = {}
        self.freq: dict[str, int] = {}
        self.order: dict[str, int] = {}
        self.tick = 0
        self.last_evicted: str | None = None

    def get(self, key: str) -> str | None:
        if key not in self.values:
            return None
        self.freq[key] += 1
        return self.values[key]

    def put(self, key: str, value: str) -> None:
        self.tick += 1
        if key in self.values:
            self.values[key] = value
            self.freq[key] += 1
            return
        if len(self.values) >= self.capacity:
            self._evict()
        self.values[key] = value
        self.freq[key] = 1
        self.order[key] = self.tick

    def _evict(self) -> None:
        victim = min(
            self.values,
            key=lambda key: (self.freq[key], self.order[key]),
        )
        del self.values[victim]
        del self.freq[victim]
        del self.order[victim]
        self.last_evicted = victim
