"""An observed-remove set: a mergeable set where a concurrent add beats a remove.

A set that replicas can edit independently and later merge runs
into a sharp question the moment one replica adds an element while
another removes it: which wins. A naive set of adds and removes
gives no stable answer, because whether the element ends up present
depends on the order the operations merge, which is exactly what a
conflict-free type must not depend on. The observed-remove set
resolves it with unique tags. Every add mints a fresh tag for the
element, and a remove does not delete the element, it tombstones
only the specific tags it has actually observed, so an element is
present whenever it owns at least one add tag that no remove has
tombstoned. This makes concurrent add-wins the rule and makes it
deterministic: a remove can only cancel the adds it saw, so an add
that happened concurrently, with a tag the remove never observed,
survives on every replica identically. Merging unions the add tags
and unions the remove tags, which is commutative and idempotent,
and the module tracks the two tag sets, decides membership by their
difference, and lets the concurrent add win the way the type
promises rather than by luck of merge order.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ORSet:
    adds: dict[str, set[str]] = field(default_factory=dict)
    removes: dict[str, set[str]] = field(default_factory=dict)

    def add(self, element: str, tag: str) -> None:
        self.adds.setdefault(element, set()).add(tag)

    def remove(self, element: str) -> None:
        observed = set(self.adds.get(element, set()))
        self.removes.setdefault(element, set()).update(observed)

    def contains(self, element: str) -> bool:
        live = self.adds.get(element, set()) - self.removes.get(
            element, set()
        )
        return bool(live)

    def elements(self) -> set[str]:
        return {
            element for element in self.adds if self.contains(element)
        }

    def merge(self, other: ORSet) -> ORSet:
        merged = ORSet()
        for element in set(self.adds) | set(other.adds):
            merged.adds[element] = self.adds.get(
                element, set()
            ) | other.adds.get(element, set())
        for element in set(self.removes) | set(other.removes):
            merged.removes[element] = self.removes.get(
                element, set()
            ) | other.removes.get(element, set())
        return merged
