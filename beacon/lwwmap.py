"""An LWW-map: a key-value map that converges key by key with last-writer-wins.

Replicating a map of key-value pairs so that independent replicas
reconcile without coordination is done by making each key a
last-writer-wins register: every write stamps its key with a
timestamp and the id of the writer, and merging two maps takes, for
each key, the value with the higher stamp, ties broken by writer id
so the choice is identical on every replica. Because each key merges
independently and deterministically, the whole map converges under
the same commutative, associative, idempotent merge that a single
LWW register enjoys, and replicas that saw the same writes agree
regardless of order. The flaw it inherits from LWW is per-key and
worth stating: two concurrent writes to the same key do not conflict
visibly, the higher timestamp simply wins and the other is lost, so
an LWW-map is right where losing one of two simultaneous edits to a
key is acceptable, a cache of settings, a presence table, and wrong
where every update must survive, which needs a map of richer merge
types. The module sets a key with a stamp, reads the current value,
and merges two maps key by key by the higher stamp.
"""

from __future__ import annotations


class LWWMap:
    def __init__(self) -> None:
        self.entries: dict[str, tuple[str, int, str]] = {}

    def set(self, key: str, value: str, timestamp: int, node: str) -> None:
        current = self.entries.get(key)
        candidate = (value, timestamp, node)
        if current is None or (timestamp, node) >= (current[1], current[2]):
            self.entries[key] = candidate

    def get(self, key: str) -> str | None:
        entry = self.entries.get(key)
        return entry[0] if entry else None

    def merge(self, other: LWWMap) -> LWWMap:
        merged = LWWMap()
        for key in set(self.entries) | set(other.entries):
            mine = self.entries.get(key)
            theirs = other.entries.get(key)
            if mine is None:
                merged.entries[key] = theirs
            elif theirs is None:
                merged.entries[key] = mine
            else:
                merged.entries[key] = (
                    mine if (mine[1], mine[2]) >= (theirs[1], theirs[2]) else theirs
                )
        return merged
