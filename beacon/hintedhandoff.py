"""Hinted handoff: hold a down replica's writes and replay them, but not without a bound.

When a write should go to a replica that is momentarily down, the
coordinator does not have to lose it or block: it stores a hint,
the write plus the replica it was meant for, and replays the hint
when the replica returns, so a brief outage becomes invisible to
the writer and no update is dropped. The danger is treating a
brief outage and a long one the same. Hints accumulate for as long
as the replica is gone, and an unbounded hint store during a
multi-hour outage becomes a second outage of its own as the
coordinator's disk fills with undelivered writes. So the store is
bounded, and when it is full the coordinator stops hinting and
lets the write fall back to the slower but unbounded path, anti-
entropy repair on the replica's return, which reconciles the whole
dataset rather than replaying a queue. The module holds the hints
per replica, refuses to store past the bound so a long outage
cannot consume unbounded space, and replays them in order on
return.
"""

from __future__ import annotations

from beacon.errors import Refused


class HintStore:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Refused(
                "a hint store of zero capacity cannot mask even a "
                "one-packet blip; give it room or do not hint"
            )
        self.capacity = capacity
        self.hints: dict[str, list[str]] = {}

    def total(self) -> int:
        return sum(len(queue) for queue in self.hints.values())

    def store(self, replica: str, write: str) -> None:
        if self.total() >= self.capacity:
            raise Refused(
                "the hint store is full; a long outage must fall "
                "back to anti-entropy repair on return, not fill "
                "the disk with undelivered writes"
            )
        self.hints.setdefault(replica, []).append(write)

    def pending(self, replica: str) -> int:
        return len(self.hints.get(replica, []))

    def replay(self, replica: str) -> list[str]:
        queued = self.hints.pop(replica, [])
        return list(queued)
