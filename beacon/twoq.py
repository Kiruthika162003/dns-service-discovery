"""The 2Q cache: a FIFO probation for newcomers, an LRU for proven items, scans pass through.

LRU is fooled by a scan and LFU clings to stale favorites, and 2Q
splits the difference with two structures. New items enter a small
FIFO queue, the probation, where they are held on trial; if an item
is accessed again while on probation it has proven itself worth
keeping and is promoted into the main LRU, the hot set, but if it is
never touched again it simply falls off the end of the FIFO without
ever polluting the LRU. That is the scan resistance: a one-time sweep
of many keys flows through the probation FIFO and out, leaving the
genuinely hot items in the main LRU untouched, exactly the failure
that flushes a plain LRU. The main queue keeps LRU's recency for the
proven set, so 2Q adapts to changing hot sets as LRU does while
resisting the scans LRU cannot. The cost is two structures and a size
split between probation and main to tune, a knob LRU does not have.
The module admits a new key to the probation FIFO, promotes a
re-accessed key into the main LRU, evicts from whichever structure is
over its bound, and reports which keys are resident, so the
scan-through behavior is observable.
"""

from __future__ import annotations

from collections import OrderedDict

from beacon.errors import Invalid


class TwoQ:
    def __init__(self, probation: int, main: int) -> None:
        if probation < 1 or main < 1:
            raise Invalid("both the probation and main sizes must be positive")
        self.probation_cap = probation
        self.main_cap = main
        self.probation: OrderedDict[str, str] = OrderedDict()
        self.main: OrderedDict[str, str] = OrderedDict()

    def access(self, key: str, value: str = "") -> None:
        if key in self.main:
            self.main.move_to_end(key)
            return
        if key in self.probation:
            promoted = self.probation.pop(key)
            self.main[key] = promoted
            self.main.move_to_end(key)
            if len(self.main) > self.main_cap:
                self.main.popitem(last=False)
            return
        self.probation[key] = value
        if len(self.probation) > self.probation_cap:
            self.probation.popitem(last=False)

    def resident(self) -> set[str]:
        return set(self.probation) | set(self.main)
