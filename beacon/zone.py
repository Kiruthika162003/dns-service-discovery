"""The authoritative zone: it knows the difference between no and not-that.

A zone answers for a subtree and its authority rests on
distinctions lazy resolvers blur. NXDOMAIN means the name does
not exist at all; NODATA means the name exists but not with
that type, and the two demand different caching, different
retries, and different debugging, so this zone raises Missing
for one and NoData for the other and never confuses them. The
CNAME rules are enforced where they are cheap, at insertion:
a name with a CNAME may hold no other data, because a name
that is an alias and also an address gives two answers to one
question, and the apex may not be an alias at all since the
zone's own SOA and NS must live somewhere. Lookups chase CNAME
chains with a loop guard, synthesize wildcard answers only
when no explicit name blocks them, and answer with referrals
below delegation points, because claiming authority past a
delegation is how two servers end up disagreeing about one
name.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Loop, Missing, NoData
from beacon.names import Name
from beacon.records import Record

MAX_CHAIN = 8


@dataclass(frozen=True)
class Soa:
    serial: int
    refresh: int
    retry: int
    expire: int
    negative_ttl: int


@dataclass
class Zone:
    apex: Name
    soa: Soa
    records: dict[tuple[str, str], list[Record]] = field(
        default_factory=dict
    )
    delegations: set[str] = field(default_factory=set)

    def _key(self, name: Name, rtype: str) -> tuple[str, str]:
        return (name.canonical(), rtype)

    def add(self, record: Record) -> None:
        if not record.name.is_subdomain_of(self.apex):
            raise Invalid(
                f"{record.name.canonical()} is outside "
                f"{self.apex.canonical()}; a zone answers only "
                "for its own subtree"
            )
        name_key = record.name.canonical()
        if record.rtype == "CNAME":
            if record.name.canonical() == self.apex.canonical():
                raise Invalid(
                    "the apex cannot be an alias; the zone's "
                    "own SOA and NS must live somewhere"
                )
            others = [
                held
                for (name, rtype), rows in self.records.items()
                if name == name_key and rtype != "CNAME"
                for held in rows
            ]
            if others:
                raise Invalid(
                    f"{name_key} already holds data; an alias "
                    "that is also an address gives two answers "
                    "to one question"
                )
        elif (name_key, "CNAME") in self.records:
            raise Invalid(
                f"{name_key} is an alias; adding "
                f"{record.rtype} beside a CNAME gives two "
                "answers to one question"
            )
        if (
            record.rtype == "NS"
            and name_key != self.apex.canonical()
        ):
            self.delegations.add(name_key)
        self.records.setdefault(
            self._key(record.name, record.rtype), []
        ).append(record)

    def _delegation_covering(self, name: Name) -> str | None:
        for ancestor in name.ancestry():
            key = ancestor.canonical()
            if (
                key in self.delegations
                and key != name.canonical()
            ):
                return key
        return None

    def _name_exists(self, name: Name) -> bool:
        target = name.canonical()
        return any(
            held == target for held, _ in self.records
        )

    def lookup(
        self, name: Name, rtype: str
    ) -> tuple[str, list[Record]]:
        if not name.is_subdomain_of(self.apex):
            raise Invalid(
                f"{name.canonical()} is not under "
                f"{self.apex.canonical()}; ask a server that "
                "answers for it"
            )
        chain: list[Record] = []
        current = name
        for _ in range(MAX_CHAIN):
            delegated = self._delegation_covering(current)
            if delegated is not None:
                referral = self.records[(delegated, "NS")]
                return "REFERRAL", chain + referral
            direct = self.records.get(self._key(current, rtype))
            if direct:
                return "ANSWER", chain + direct
            alias = self.records.get(
                self._key(current, "CNAME")
            )
            if alias:
                chain = chain + alias
                current = alias[0].value
                if not current.is_subdomain_of(self.apex):
                    return "ANSWER", chain
                continue
            synthesized = self._wildcard_answer(current, rtype)
            if synthesized is not None:
                return "ANSWER", chain + synthesized
            if self._name_exists(current):
                raise NoData(
                    f"{current.canonical()} exists but holds "
                    f"no {rtype}; not-that is a different "
                    "answer from no"
                )
            raise Missing(
                f"{current.canonical()} does not exist in "
                f"{self.apex.canonical()} (negative ttl "
                f"{self.soa.negative_ttl})"
            )
        raise Loop(
            f"the CNAME chain from {name.canonical()} exceeds "
            f"{MAX_CHAIN} links; aliases pointing in circles"
        )

    def _wildcard_answer(
        self, name: Name, rtype: str
    ) -> list[Record] | None:
        if self._name_exists(name):
            return None
        for ancestor in name.ancestry()[1:]:
            star = Name(labels=("*", *ancestor.labels))
            rows = self.records.get(self._key(star, rtype))
            if rows and star.wildcard_matches(name):
                return [
                    Record(
                        name=name,
                        rtype=row.rtype,
                        value=row.value,
                        ttl=row.ttl,
                    )
                    for row in rows
                ]
            if self._name_exists(star):
                return None
        return None
