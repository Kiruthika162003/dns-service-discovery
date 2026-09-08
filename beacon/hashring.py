"""The consistent hash ring: members come and go, keys mostly stay put.

Assigning keys to members by modulo reshuffles nearly
everything when the member count changes, which is the wrong
property for caches and ownership alike. The ring fixes it by
hashing both keys and members onto a circle: a key belongs to
the first member clockwise from it, so when a member leaves,
only the keys it owned move, and when one joins, it takes an
arc from its clockwise neighbor and nobody else notices.
Virtual nodes are the balance repair: one point per member
makes arc sizes a lottery, many points per member average the
luck out, and the spread report measures the largest share
against the fairest possible, because "the ring balances" is
a claim with a number and the number depends on the vnode
count in a way worth seeing rather than trusting. Every
movement claim here is measured by comparing full ownership
maps before and after, not asserted from theory.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing


def _point(text: str) -> int:
    return int(
        hashlib.sha256(text.encode()).hexdigest()[:8], 16
    )


@dataclass
class HashRing:
    vnodes: int = 64
    points: dict[int, str] = field(default_factory=dict)
    members: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.vnodes < 1:
            raise Invalid("a ring needs at least one point per member")

    def join(self, member: str) -> None:
        if member in self.members:
            raise Invalid(f"{member} is already on the ring")
        self.members.add(member)
        for index in range(self.vnodes):
            self.points[_point(f"{member}#{index}")] = member

    def leave(self, member: str) -> None:
        if member not in self.members:
            raise Missing(f"{member} is not on the ring")
        self.members.remove(member)
        self.points = {
            point: owner
            for point, owner in self.points.items()
            if owner != member
        }

    def owner_of(self, key: str) -> str:
        if not self.points:
            raise Missing("an empty ring owns nothing")
        target = _point(key)
        ordered = sorted(self.points)
        for point in ordered:
            if point >= target:
                return self.points[point]
        return self.points[ordered[0]]

    def ownership_map(self, keys: list[str]) -> dict[str, str]:
        return {key: self.owner_of(key) for key in keys}

    def spread_report(self, keys: list[str]) -> str:
        if not keys:
            raise Invalid("no keys to spread")
        counts: dict[str, int] = dict.fromkeys(self.members, 0)
        for key in keys:
            counts[self.owner_of(key)] += 1
        fair = len(keys) / len(self.members)
        heaviest = max(counts.values())
        lightest = min(counts.values())
        return (
            f"{len(keys)} key(s) over {len(self.members)} "
            f"member(s) at {self.vnodes} vnode(s): heaviest "
            f"{heaviest}, lightest {lightest}, fair share "
            f"{fair:.0f}; balance is a number, not a claim"
        )


def movement_on_change(
    before: dict[str, str], after: dict[str, str]
) -> tuple[int, float]:
    if before.keys() != after.keys():
        raise Invalid("compare the same key set or nothing")
    moved = sum(
        1 for key in before if before[key] != after[key]
    )
    return moved, moved / len(before)
