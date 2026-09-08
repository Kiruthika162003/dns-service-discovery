"""A multi-value register: keep every concurrent write rather than silently losing one.

The last-writer-wins register resolves concurrent writes by keeping
the one with the higher timestamp and discarding the other, which is
simple but destroys data whenever two replicas wrote at once. A
multi-value register refuses that loss. Each write carries a version
vector describing what the writer had seen, and the register keeps a
value for every write that is not superseded by another, so a write
that dominates an existing value replaces it, but two writes that are
concurrent, neither having seen the other, are both retained. A read
therefore returns not one value but the set of currently concurrent
values, and it is the application's job to merge them, choosing, or
combining, or presenting the conflict, rather than the register
pretending there was no conflict at all. That is the honest trade:
the multi-value register never loses a write to a coin flip of
magnitude, at the cost that a read can hand back several values the
caller must reconcile, where last-writer-wins hands back exactly one
and hopes it was the right one. The module writes a value with its
version vector, dropping the entries it dominates and keeping the
concurrent ones, and reads the current value set, so a genuine
conflict surfaces instead of vanishing.
"""

from __future__ import annotations

from beacon.versionvector import compare


class MVRegister:
    def __init__(self) -> None:
        self.entries: list[tuple[str, dict[str, int]]] = []

    def write(self, value: str, version: dict[str, int]) -> None:
        survivors: list[tuple[str, dict[str, int]]] = []
        superseded_by_existing = False
        for existing_value, existing_vv in self.entries:
            verdict = compare(version, existing_vv)
            if verdict == "right-dominates":
                survivors.append((existing_value, existing_vv))
                superseded_by_existing = True
            elif verdict == "concurrent":
                survivors.append((existing_value, existing_vv))
            # left-dominates or equal: the new write supersedes it, drop
        if not superseded_by_existing:
            survivors.append((value, dict(version)))
        self.entries = survivors

    def read(self) -> list[str]:
        return sorted(value for value, _ in self.entries)

    def has_conflict(self) -> bool:
        return len(self.entries) > 1
