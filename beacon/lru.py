"""An LRU cache: evict the least recently used, betting that recency predicts reuse.

A bounded cache has to choose what to drop when it fills, and the
least-recently-used policy makes the simplest defensible bet: the
entry nobody has touched for the longest is the one least likely to
be wanted next, so it goes first. It is cheap to maintain, every
access moves an entry to the most-recent end and eviction takes
from the least-recent end, and for the ordinary workload where hot
keys are hit repeatedly it keeps exactly those in cache. The bet
has a known failure that the module names rather than hides: a scan,
a one-time sweep over many keys that will never be seen again,
walks in as the most-recently-used and pushes the genuinely hot set
out the least-recent end, so a single large scan can evict the
working set the cache existed to hold. That is why scan-resistant
policies exist, and admitting the weakness is the honest framing
for choosing LRU only where scans are rare. The module tracks the
recency order, serves and promotes on a hit, evicts the oldest when
over capacity, and remembers what it evicted so the pressure is
observable.
"""

from __future__ import annotations

from collections import OrderedDict

from beacon.errors import Invalid


class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid(
                "a cache of zero capacity holds nothing and is a "
                "miss on every lookup, not a cache"
            )
        self.capacity = capacity
        self.store: OrderedDict[str, str] = OrderedDict()
        self.last_evicted: str | None = None

    def get(self, key: str) -> str | None:
        if key not in self.store:
            return None
        self.store.move_to_end(key)
        return self.store[key]

    def put(self, key: str, value: str) -> None:
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            evicted, _ = self.store.popitem(last=False)
            self.last_evicted = evicted

    def order(self) -> list[str]:
        return list(self.store)
