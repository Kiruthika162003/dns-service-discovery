"""Hybrid logical clocks: causality like Lamport, but pinned within a hair of the wall clock.

A Lamport clock preserves happens-before but drifts arbitrarily
far from real time, so its timestamps are useless for asking when
did this happen, and a raw physical clock answers when but breaks
causality whenever two nodes' clocks disagree, which they always
do a little. A hybrid logical clock takes both. It carries a
physical component and a small logical counter, and it advances the
physical part to track the wall clock while using the logical part
only to break ties when events share a physical instant or when a
message arrives stamped with a physical time ahead of the local
clock. The result is a timestamp that never runs more than the
clock skew ahead of real time, so it doubles as an approximate
wall-clock reading, yet still guarantees that a message's receive
stamp exceeds its send stamp, so causality holds. The logical
counter only grows during ties and resets the moment the physical
clock moves forward, which keeps it small and bounded. The module
implements the local and receive update rules and holds the
invariant that the stamp never regresses, since a clock that went
backward would let a later event look earlier.
"""

from __future__ import annotations

from beacon.errors import Invalid


class HybridClock:
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self.wall = 0
        self.logical = 0

    def local(self, physical_time: int) -> tuple[int, int]:
        if physical_time > self.wall:
            self.wall = physical_time
            self.logical = 0
        else:
            self.logical += 1
        return (self.wall, self.logical)

    def receive(
        self, physical_time: int, msg_wall: int, msg_logical: int
    ) -> tuple[int, int]:
        new_wall = max(self.wall, msg_wall, physical_time)
        if new_wall == self.wall == msg_wall:
            self.logical = max(self.logical, msg_logical) + 1
        elif new_wall == self.wall:
            self.logical += 1
        elif new_wall == msg_wall:
            self.logical = msg_logical + 1
        else:
            self.logical = 0
        self.wall = new_wall
        return (self.wall, self.logical)

    def drift_from_physical(self, physical_time: int) -> int:
        drift = self.wall - physical_time
        if drift < 0:
            raise Invalid(
                "the hybrid clock is behind physical time, which "
                "its update rules forbid; a stamp that lagged the "
                "wall clock would misreport when an event happened"
            )
        return drift
