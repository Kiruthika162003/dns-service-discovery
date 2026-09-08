"""Catalog zones: one zone that lists the zones a secondary should serve, synced automatically.

A secondary name server that hosts thousands of zones cannot have
each one added and removed by hand on every server, so RFC 9432
turns the list itself into a zone. The catalog zone is an ordinary
zone with a schema: a version marker and, under a member label, a
PTR from a unique per-member label to each member zone's name.
The secondary transfers the catalog like any other zone and then
reconciles, adding the members that appear and dropping the ones
that have vanished, so provisioning becomes a data change in one
place instead of a config push everywhere. The module enforces
the schema version it understands, because a catalog written to a
newer schema might mean things this secondary would misread, and
it refuses a catalog that lists one zone under two labels, since a
member identified twice is an ambiguity the reconcile cannot
resolve without guessing which label is authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

SUPPORTED_VERSION = 2


@dataclass
class Catalog:
    version: int
    members: dict[str, str]

    def __post_init__(self) -> None:
        if self.version != SUPPORTED_VERSION:
            raise Invalid(
                f"catalog schema version {self.version} is not the "
                f"{SUPPORTED_VERSION} this secondary understands; a "
                "newer schema might mean things it would misread"
            )
        seen = set()
        for zone in self.members.values():
            if zone in seen:
                raise Invalid(
                    f"{zone} is listed under two labels; a member "
                    "identified twice is an ambiguity the reconcile "
                    "cannot resolve without guessing"
                )
            seen.add(zone)

    def zones(self) -> set[str]:
        return set(self.members.values())


def reconcile(
    current: set[str], catalog: Catalog
) -> tuple[set[str], set[str]]:
    desired = catalog.zones()
    to_add = desired - current
    to_remove = current - desired
    return to_add, to_remove


def summary(current: set[str], catalog: Catalog) -> str:
    to_add, to_remove = reconcile(current, catalog)
    return (
        f"catalog v{catalog.version}: add {len(to_add)}, remove "
        f"{len(to_remove)}, to reach {len(catalog.zones())} "
        "member zone(s) without a config push"
    )
