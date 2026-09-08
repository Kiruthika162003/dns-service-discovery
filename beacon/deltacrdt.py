"""A delta-state CRDT: ship the change, not the whole state, and still converge.

A state-based CRDT converges by having replicas exchange their full
state and merge, which is beautifully simple and increasingly
wasteful: as the state grows, every sync ships the entire thing even
though only a little changed since the last one. A delta-state CRDT
keeps the same convergence guarantee while shipping only the
difference. Each mutation produces a delta, itself a tiny CRDT
holding just the entry that changed, and a replica applies a delta
with the very same merge, the join, that it would use on a full
state, so a delta merges correctly whether it arrives once, twice,
or out of order. The bandwidth drops from the size of the state to
the size of the change, which for a large counter touched in one
place is the difference between shipping one entry and shipping
thousands. The cost, stated honestly, is bookkeeping: a replica must
track which deltas a peer has acknowledged so it knows what still
needs sending, where the full-state approach was stateless about
what to send because it always sent everything. The module models a
delta grow-only counter, producing a single-entry delta on
increment and merging deltas by the entrywise maximum the join
requires.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DeltaGCounter:
    counts: dict[str, int] = field(default_factory=dict)

    def increment(self, replica: str, by: int = 1) -> dict[str, int]:
        self.counts[replica] = self.counts.get(replica, 0) + by
        return {replica: self.counts[replica]}

    def merge_delta(self, delta: dict[str, int]) -> None:
        for replica, count in delta.items():
            self.counts[replica] = max(
                self.counts.get(replica, 0), count
            )

    def value(self) -> int:
        return sum(self.counts.values())
