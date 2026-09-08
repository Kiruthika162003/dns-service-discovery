"""A two-phase set: removal by permanent tombstone, so a removed element can never return.

The grow-only set cannot remove, and the two-phase set adds removal
in the simplest way that stays a conflict-free type: two grow-only
sets, one of added elements and one of removed elements, tombstones,
with an element considered present when it is in the added set and
not in the removed set. Both underlying sets only grow, so merging is
the union of the added sets and the union of the removed sets, which
converges without coordination just as a grow-only set does. The
consequence, and the honest limit, is that removal is permanent: once
an element is in the tombstone set it stays there, so the element can
never be added back, because a later add cannot outweigh the tombstone
under this scheme. That is simpler than the observed-remove set, which
uses per-add tags precisely so an element can be re-added, and it is
strictly weaker for the same reason, the trade being no tag machinery
in exchange for no re-adding. It fits data where removal is final, a
revoked credential, a decommissioned node, and misfits anything that
churns. The module adds and removes, decides membership as added-and-
not-tombstoned, refuses re-adding a tombstoned element, and merges by
unioning both underlying sets.
"""

from __future__ import annotations

from beacon.errors import Invalid


class TwoPhaseSet:
    def __init__(self) -> None:
        self.added: set[str] = set()
        self.removed: set[str] = set()

    def add(self, element: str) -> None:
        if element in self.removed:
            raise Invalid(
                f"{element} is tombstoned and cannot be re-added; a "
                "two-phase set makes removal permanent, use an OR-set "
                "to re-add"
            )
        self.added.add(element)

    def remove(self, element: str) -> None:
        if element not in self.added:
            raise Invalid(
                f"{element} was never added, so there is nothing to "
                "remove"
            )
        self.removed.add(element)

    def contains(self, element: str) -> bool:
        return element in self.added and element not in self.removed

    def merge(self, other: TwoPhaseSet) -> TwoPhaseSet:
        merged = TwoPhaseSet()
        merged.added = self.added | other.added
        merged.removed = self.removed | other.removed
        return merged
