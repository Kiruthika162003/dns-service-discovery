"""A grow-only set: the simplest CRDT, where merge is union and convergence is free.

The grow-only set is the plainest conflict-free replicated data type
and worth having on its own because so much is built from it. It
supports only addition, and merging two replicas is simply the union
of their elements, which is commutative, associative, and idempotent,
so replicas that have seen the same additions in any order, with any
duplication, converge on the identical set with no coordination and
no possibility of conflict. That is the whole appeal: for anything
that only ever accumulates, a set of nodes ever seen, of features ever
enabled, of shards ever created, a grow-only set is correct and
trivial. Its limitation is equally plain and is the reason richer
types exist: it cannot remove, because removal is not expressible as
a union and would break the convergence the union guarantees, so a
value once added is permanent. Anything needing removal must move to
a two-phase set, which allows a permanent tombstone, or an
observed-remove set, which allows re-adding, each carrying more
machinery than the bare union. The module adds an element, tests
membership, and merges by union, the operation that makes it a CRDT.
"""

from __future__ import annotations


class GSet:
    def __init__(self) -> None:
        self.elements: set[str] = set()

    def add(self, element: str) -> None:
        self.elements.add(element)

    def contains(self, element: str) -> bool:
        return element in self.elements

    def merge(self, other: GSet) -> GSet:
        merged = GSet()
        merged.elements = self.elements | other.elements
        return merged

    def as_set(self) -> set[str]:
        return set(self.elements)
