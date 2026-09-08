"""Adaptive Replacement Cache: self-tune the recency-frequency split from the misses.

LRU protects recency and is fooled by frequency, LFU the reverse, and
2Q fixes a split between them at a tuned constant. ARC makes that
split adaptive, tuning itself from the workload rather than a knob.
It keeps two live lists, one of pages seen once recently and one of
pages seen at least twice, and crucially two ghost lists, remembering
the keys recently evicted from each, holding no data. A miss whose key
sits in the recency ghost list is evidence the cache is too biased
toward frequency and should grow its recency half, so ARC nudges its
target boundary that way, and a miss in the frequency ghost list
nudges it the other, so the cache continuously rebalances toward
whichever pattern the recent misses show it is underserving. That
adaptivity is the point: a workload that shifts from scanning to
repeated access, or back, is followed without reconfiguration, where
LRU, LFU, and a fixed 2Q each stay committed to their one bet. The
cost is the bookkeeping of four lists and the ghost history. The
module implements the access with the ghost-driven adaptation and the
replacement that honors the moving target, holding capacity so the
live entries never exceed it, so the self-tuning is observable rather
than asserted.
"""

from __future__ import annotations

from collections import OrderedDict

from beacon.errors import Invalid


class ARC:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a cache of zero capacity holds nothing")
        self.c = capacity
        self.p = 0
        self.t1: OrderedDict[str, str] = OrderedDict()
        self.t2: OrderedDict[str, str] = OrderedDict()
        self.b1: OrderedDict[str, None] = OrderedDict()
        self.b2: OrderedDict[str, None] = OrderedDict()

    def _replace(self, in_b2: bool) -> None:
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            key, _ = self.t1.popitem(last=False)
            self.b1[key] = None
        elif self.t2:
            key, _ = self.t2.popitem(last=False)
            self.b2[key] = None

    def access(self, key: str, value: str = "") -> None:
        if key in self.t1:
            del self.t1[key]
            self.t2[key] = value
            return
        if key in self.t2:
            self.t2.move_to_end(key)
            return
        if key in self.b1:
            self.p = min(self.c, self.p + max(1, len(self.b2) // max(1, len(self.b1))))
            self._replace(in_b2=False)
            del self.b1[key]
            self.t2[key] = value
            return
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // max(1, len(self.b2))))
            self._replace(in_b2=True)
            del self.b2[key]
            self.t2[key] = value
            return
        if len(self.t1) + len(self.b1) == self.c:
            if len(self.t1) < self.c:
                self.b1.popitem(last=False)
                self._replace(in_b2=False)
            else:
                self.t1.popitem(last=False)
        elif len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2) >= self.c:
            if len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2) == 2 * self.c:
                self.b2.popitem(last=False)
            self._replace(in_b2=False)
        self.t1[key] = value

    def resident(self) -> set[str]:
        return set(self.t1) | set(self.t2)
