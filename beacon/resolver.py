"""The recursive resolver: it walks referrals so its callers never have to.

Resolution is a guided descent: ask the nearest authority,
follow referrals downward, chase CNAMEs sideways, and remember
everything learned on the way, positive and negative alike.
The cache is consulted before any query travels, and every
upstream answer is written back with its distinction intact,
which is where recursive resolvers earn their keep: the second
asker of a dead name costs nothing because the first asker's
NXDOMAIN was cached under the zone's negative TTL. The
resolver counts its upstream queries per resolution and the
depth of each descent, because a resolution that took nine
queries is a topology complaint waiting to be filed, and the
referral limit converts a delegation cycle between two lazy
zones from an infinite loop into a named refusal.

The first descent test guessed two queries for a child-zone
answer; the measurement says one, because authority selection
walks the name's ancestry to the deepest hosted zone before
any query travels, so hosting the child makes the descent
free. Referrals earn their keep only at the boundary, when a
delegation points at a zone this resolver does not host, and
the wrong guess stays here because it documents where the
hops actually live.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.cache import TtlCache
from beacon.errors import Loop, Missing, NoData, Refused
from beacon.names import Name
from beacon.records import Record
from beacon.zone import Zone

MAX_REFERRALS = 8


@dataclass
class Resolution:
    status: str
    records: list[Record]
    upstream_queries: int
    from_cache: bool


@dataclass
class Resolver:
    zones: dict[str, Zone] = field(default_factory=dict)
    cache: TtlCache = field(default_factory=TtlCache)
    upstream_total: int = 0

    def host_zone(self, zone: Zone) -> None:
        self.zones[zone.apex.canonical()] = zone

    def _authority_for(self, name: Name) -> Zone:
        for ancestor in name.ancestry():
            zone = self.zones.get(ancestor.canonical())
            if zone is not None:
                return zone
        raise Refused(
            f"no hosted zone answers for {name.canonical()}; "
            "this resolver refuses rather than inventing"
        )

    def resolve(
        self, name: Name, rtype: str, now: int
    ) -> Resolution:
        cached = self.cache.lookup(name, rtype, now)
        if cached is not None:
            kind, records, _ = cached
            if kind == "NXDOMAIN":
                raise Missing(
                    f"{name.canonical()} does not exist "
                    "(remembered; nothing travelled)"
                )
            if kind == "NODATA":
                raise NoData(
                    f"{name.canonical()} holds no {rtype} "
                    "(remembered; nothing travelled)"
                )
            return Resolution(
                status="ANSWER",
                records=records,
                upstream_queries=0,
                from_cache=True,
            )
        queries = 0
        zone = self._authority_for(name)
        current = name
        for _ in range(MAX_REFERRALS):
            queries += 1
            self.upstream_total += 1
            try:
                status, rows = zone.lookup(current, rtype)
            except Missing:
                self.cache.store_negative(
                    current,
                    "NXDOMAIN",
                    now=now,
                    negative_ttl=zone.soa.negative_ttl,
                )
                raise
            except NoData:
                self.cache.store_negative(
                    current,
                    "NODATA",
                    now=now,
                    negative_ttl=zone.soa.negative_ttl,
                    rtype=rtype,
                )
                raise
            if status == "ANSWER":
                answer_rows = [
                    row for row in rows if row.rtype == rtype
                ]
                if answer_rows:
                    self.cache.store(
                        current if answer_rows else name,
                        rtype,
                        answer_rows,
                        now=now,
                    )
                final = rows[-1]
                if final.rtype == "CNAME" and not answer_rows:
                    target = final.value
                    zone = self._authority_for(target)
                    current = target
                    continue
                return Resolution(
                    status="ANSWER",
                    records=rows,
                    upstream_queries=queries,
                    from_cache=False,
                )
            referral_target = rows[-1].name
            child = self.zones.get(referral_target.canonical())
            if child is None:
                raise Refused(
                    f"referred to {referral_target.canonical()} "
                    "but no such zone is hosted here; the "
                    "delegation points into the dark"
                )
            zone = child
        raise Loop(
            f"{MAX_REFERRALS} referrals without an answer; a "
            "delegation cycle between lazy zones, refused by "
            "name instead of looped forever"
        )

    def descent_report(self) -> str:
        return (
            f"{self.upstream_total} upstream query(ies) total; "
            f"{self.cache.ledger()}"
        )
