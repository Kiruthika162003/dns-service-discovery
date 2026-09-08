"""A last-writer-wins register: a mergeable cell where the newest write survives a merge.

When two replicas each hold a value for the same key and later
reconcile, something must decide which value wins, and a
last-writer-wins register decides by timestamp: each write is
tagged with the time it happened and the id of the replica that
made it, and merging two registers keeps the one with the higher
tag. The register is a conflict-free replicated data type because
that merge is commutative, associative, and idempotent, so
replicas that see the same set of writes in any order converge on
the same value with no coordination. The honesty the module keeps
is about the tie: two writes can carry the same timestamp, and a
timestamp alone would leave the merge undefined and therefore
divergent, so the replica id breaks the tie deterministically,
which means a same-instant write from a higher-id replica wins on
every node identically. That is a real choice with a real cost,
last-writer-wins silently discards the losing write rather than
surfacing it as a conflict the way a version vector would, and the
module names that so the register is chosen for the cases where
losing an update is acceptable, not assumed to be safe everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LWWRegister:
    value: str
    timestamp: int
    node: str

    def _tag(self) -> tuple[int, str]:
        return (self.timestamp, self.node)

    def merge(self, other: LWWRegister) -> LWWRegister:
        return self if self._tag() >= other._tag() else other

    def assign(
        self, value: str, timestamp: int, node: str
    ) -> LWWRegister:
        candidate = LWWRegister(value, timestamp, node)
        return self.merge(candidate)
