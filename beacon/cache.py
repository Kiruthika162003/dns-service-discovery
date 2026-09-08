"""The TTL cache: answers age, and a cache that forgets that serves lies.

Every cached answer carries the tick it was stored and the TTL
it arrived with, and every read pays rent: the remaining TTL is
computed against the asker's now, expired entries are evicted
on contact rather than returned, and a hit is served with its
remaining lifetime, not the original, because a downstream
cache that re-serves the full TTL mints immortal records one
hop at a time, the oldest amplification bug in DNS. Negative
answers cache too, under the zone's negative TTL, and are
stored as the distinction they arrived with: an NXDOMAIN entry
answers for every type at that name while a NODATA entry
answers only for the type that was absent, since flattening
the two poisons the name for types that were never asked. The
ledger counts hits, misses, expiries on contact, and the
negative saves, the queries that never had to travel because
the cache remembered a no.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid
from beacon.names import Name
from beacon.records import Record


@dataclass
class CachedAnswer:
    records: list[Record]
    stored_at: int
    ttl: int


@dataclass
class NegativeEntry:
    kind: str
    rtype: str | None
    stored_at: int
    ttl: int


@dataclass
class TtlCache:
    answers: dict[tuple[str, str], CachedAnswer] = field(
        default_factory=dict
    )
    negatives: dict[str, list[NegativeEntry]] = field(
        default_factory=dict
    )
    hits: int = 0
    misses: int = 0
    expiries_on_contact: int = 0
    negative_saves: int = 0

    def store(
        self, name: Name, rtype: str, records: list[Record], now: int
    ) -> str:
        if not records:
            raise Invalid(
                "an empty answer is a negative; store it as one"
            )
        ttl = min(record.ttl for record in records)
        if ttl == 0:
            return (
                f"{name.canonical()} {rtype}: ttl 0 means "
                "do-not-cache, and the cache does not"
            )
        self.answers[(name.canonical(), rtype)] = CachedAnswer(
            records=list(records), stored_at=now, ttl=ttl
        )
        return (
            f"{name.canonical()} {rtype}: cached for {ttl} "
            "tick(s), the smallest ttl in the set"
        )

    def store_negative(
        self,
        name: Name,
        kind: str,
        now: int,
        negative_ttl: int,
        rtype: str | None = None,
    ) -> None:
        if kind not in ("NXDOMAIN", "NODATA"):
            raise Invalid(f"{kind} is not a negative kind")
        if kind == "NODATA" and rtype is None:
            raise Invalid(
                "NODATA is about one type; name it, or the "
                "entry poisons types never asked"
            )
        self.negatives.setdefault(name.canonical(), []).append(
            NegativeEntry(
                kind=kind,
                rtype=rtype if kind == "NODATA" else None,
                stored_at=now,
                ttl=negative_ttl,
            )
        )

    def lookup(
        self, name: Name, rtype: str, now: int
    ) -> tuple[str, list[Record], int] | None:
        key = name.canonical()
        for entry in list(self.negatives.get(key, [])):
            if now >= entry.stored_at + entry.ttl:
                self.negatives[key].remove(entry)
                self.expiries_on_contact += 1
                continue
            if entry.kind == "NXDOMAIN" or entry.rtype == rtype:
                self.negative_saves += 1
                remaining = entry.stored_at + entry.ttl - now
                return (entry.kind, [], remaining)
        held = self.answers.get((key, rtype))
        if held is None:
            self.misses += 1
            return None
        remaining = held.stored_at + held.ttl - now
        if remaining <= 0:
            del self.answers[(key, rtype)]
            self.expiries_on_contact += 1
            self.misses += 1
            return None
        self.hits += 1
        return ("ANSWER", held.records, remaining)

    def ledger(self) -> str:
        return (
            f"{self.hits} hit(s), {self.misses} miss(es), "
            f"{self.expiries_on_contact} expiry(ies) on "
            f"contact, {self.negative_saves} negative save(s): "
            "queries that never travelled because the cache "
            "remembered a no"
        )
