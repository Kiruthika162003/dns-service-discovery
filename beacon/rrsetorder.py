"""One RRset, one TTL: the records of a set share a lifetime or the cache splits them.

All records of the same name and type form an RRset, and the
protocol treats the set as atomic: a resolver caches it as a
unit and hands it back as a unit. That only holds if the records
agree on how long they live, so when an authority is configured
with mismatched TTLs on one set, the honest repair is to clamp
them all to the minimum, because the alternative, letting each
record expire on its own clock, would let the set fracture in
mid-cache into a subset no client should ever see, half the
addresses fresh and half already gone. The clamp is to the
minimum and not the maximum on purpose: the smallest TTL is the
value one record's owner declared as the most volatile, and
serving the others past that point would outlive the freshness
promise the set as a whole is able to keep. The module reports
which records were shortened, since a silent clamp hides a
misconfiguration the operator should still go fix at the source.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class Harmonized:
    ttl: int
    shortened: int
    original: tuple[int, ...]

    def report(self) -> str:
        if self.shortened == 0:
            return (
                f"the set already agreed at {self.ttl}s; nothing "
                "to clamp"
            )
        return (
            f"clamped the set to {self.ttl}s, shortening "
            f"{self.shortened} record(s) whose TTL disagreed; "
            "the mismatch is still a config bug to fix at source"
        )


def harmonize(ttls: list[int]) -> Harmonized:
    if not ttls:
        raise Invalid("an empty RRset has no TTL to harmonize")
    for value in ttls:
        if value < 0:
            raise Invalid(
                f"a TTL of {value} is negative; a record cannot "
                "have lived for less than no time"
            )
    floor = min(ttls)
    shortened = sum(1 for value in ttls if value > floor)
    return Harmonized(floor, shortened, tuple(ttls))
