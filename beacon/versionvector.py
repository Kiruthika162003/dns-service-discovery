"""Version vectors: telling a true conflict from a stale copy that a lone counter cannot.

If two replicas each track a value with a single version number,
they can compare which is higher and keep it, but that comparison
silently destroys data whenever both were edited independently:
the higher number wins and the other edit vanishes, though nothing
made it less valid. A version vector keeps a counter per replica
instead of one shared number, so an update increments only the
editing replica's entry, and comparing two vectors distinguishes
four cases a scalar cannot. One vector may dominate the other,
every entry at least as high and one higher, which means it is a
strict descendant and the older copy can be dropped safely. Or
neither dominates, each ahead on its own replica's entry, which
means the two were edited concurrently and there is a real
conflict that must be surfaced, not silently resolved by a
coin-flip of magnitude. The module reports which of equal,
dominating, or concurrent holds, and merges two vectors by taking
the entrywise maximum, because the merge must remember everything
both sides ever saw or it would reintroduce a conflict already
settled.
"""

from __future__ import annotations

from beacon.errors import Invalid


def increment(
    vector: dict[str, int], replica: str
) -> dict[str, int]:
    updated = dict(vector)
    updated[replica] = updated.get(replica, 0) + 1
    return updated


def compare(
    left: dict[str, int], right: dict[str, int]
) -> str:
    keys = set(left) | set(right)
    left_ahead = False
    right_ahead = False
    for key in keys:
        lv = left.get(key, 0)
        rv = right.get(key, 0)
        if lv > rv:
            left_ahead = True
        elif rv > lv:
            right_ahead = True
    if left_ahead and right_ahead:
        return "concurrent"
    if left_ahead:
        return "left-dominates"
    if right_ahead:
        return "right-dominates"
    return "equal"


def merge(
    left: dict[str, int], right: dict[str, int]
) -> dict[str, int]:
    keys = set(left) | set(right)
    return {
        key: max(left.get(key, 0), right.get(key, 0)) for key in keys
    }


def is_conflict(
    left: dict[str, int], right: dict[str, int]
) -> bool:
    return compare(left, right) == "concurrent"


def descends_from(
    descendant: dict[str, int], ancestor: dict[str, int]
) -> bool:
    verdict = compare(descendant, ancestor)
    if verdict == "concurrent":
        raise Invalid(
            "the two vectors are concurrent, so neither descends "
            "from the other; this is a conflict, not a lineage"
        )
    return verdict in ("left-dominates", "equal")
