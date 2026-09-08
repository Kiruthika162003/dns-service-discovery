"""Tombstones: the dead stay dead even when old rumors say otherwise.

Gossip has no delivery order, so a deregistration can race its
own registration around the cluster: node A removes a service,
node B still carries the old entry, and B's next gossip round
politely resurrects what A just buried. The tombstone is the
fix: deletion is not the absence of a record but a record of
absence, carrying the deletion's version, and any merge that
sees both the entry and its tombstone lets the higher version
win, which means the ghost bounces off the grave marker
instead of walking. The cost is that graves take memory, so
tombstones are reaped, but only after the gossip horizon, the
time by which every peer must have heard, because a grave
reaped early is exactly a resurrection permit, and the reaper
counts what it holds so the memory bill of remembering the
dead is a number on a page instead of a slow surprise.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

GOSSIP_HORIZON = 60


@dataclass
class Grave:
    key: str
    version: int
    buried_at: int


@dataclass
class TombstoneStore:
    living: dict[str, int] = field(default_factory=dict)
    graves: dict[str, Grave] = field(default_factory=dict)
    resurrections_blocked: int = 0
    reaped: int = 0

    def register(self, key: str, version: int) -> str:
        grave = self.graves.get(key)
        if grave is not None and grave.version >= version:
            self.resurrections_blocked += 1
            return (
                f"{key} at version {version} bounced off the "
                f"grave marker (buried at version "
                f"{grave.version}); the ghost does not walk"
            )
        if grave is not None:
            del self.graves[key]
        self.living[key] = version
        return f"{key} registered at version {version}"

    def deregister(self, key: str, version: int, now: int) -> str:
        held = self.living.get(key)
        if held is None and key not in self.graves:
            raise Invalid(
                f"{key} was never here; burying nothing digs "
                "a hole for no reason"
            )
        if held is not None and version < held:
            raise Invalid(
                f"{key}: a deletion at version {version} "
                f"cannot bury a newer registration at {held}"
            )
        self.living.pop(key, None)
        self.graves[key] = Grave(
            key=key, version=version, buried_at=now
        )
        return (
            f"{key} buried at version {version}; deletion is "
            "a record of absence, not an absence of record"
        )

    def merge_rumor(self, key: str, version: int) -> str:
        return self.register(key, version)

    def reap(self, now: int) -> str:
        ready = [
            grave
            for grave in self.graves.values()
            if now - grave.buried_at >= GOSSIP_HORIZON
        ]
        for grave in ready:
            del self.graves[grave.key]
            self.reaped += 1
        kept = len(self.graves)
        return (
            f"{len(ready)} grave(s) reaped past the "
            f"{GOSSIP_HORIZON}-tick horizon, {kept} still "
            "held; a grave reaped early is a resurrection "
            "permit"
        )

    def memory_bill(self) -> str:
        return (
            f"{len(self.living)} living, {len(self.graves)} "
            f"grave(s) held, {self.reaped} reaped, "
            f"{self.resurrections_blocked} resurrection(s) "
            "blocked; remembering the dead costs memory and "
            "the bill is this line"
        )
