"""A grow-only counter CRDT: many replicas count independently and merge without a total lost.

Counting across replicas is deceptively hard: if each just holds a
running total and merging takes the larger, every increment that
happened on the smaller replica is erased. A grow-only counter
avoids the loss by never sharing a single total. Each replica keeps
its own per-replica tally and only ever increments its own entry,
so the entries never conflict, and the counter's value is the sum
of all entries. Merging two counters takes the entrywise maximum,
which is safe precisely because each entry only grows: the maximum
of a replica's own tally across two copies is simply its latest
value, so no increment is double-counted and none is dropped. That
makes the merge commutative, associative, and idempotent, and the
replicas converge with no coordination. The cost, stated plainly,
is that the counter can only grow, because allowing decrements
would break the entries-only-increase invariant the merge relies
on, and the module refuses a negative increment rather than
silently corrupting the merge. Decrements need a second counter,
which is a different type.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class GCounter:
    counts: dict[str, int] = field(default_factory=dict)

    def increment(self, replica: str, by: int = 1) -> None:
        if by < 0:
            raise Invalid(
                "a grow-only counter cannot decrement; a negative "
                "increment would break the entries-only-increase "
                "invariant the merge depends on. Use a PN-counter"
            )
        self.counts[replica] = self.counts.get(replica, 0) + by

    def value(self) -> int:
        return sum(self.counts.values())

    def merge(self, other: GCounter) -> GCounter:
        keys = set(self.counts) | set(other.counts)
        merged = {
            key: max(self.counts.get(key, 0), other.counts.get(key, 0))
            for key in keys
        }
        return GCounter(merged)
