"""Aggressive negative caching: one signed no can answer for a whole range.

A signed NSEC record proves that nothing exists between two
names, and that proof is stronger than a single NXDOMAIN: it
answers for every name in the gap, not just the one asked. A
resolver that caches the signed range can answer future
queries for any name that sorts inside it without asking the
authority again, which turns a random-subdomain flood, the
attack that hammers an authority with thousands of guaranteed-
nonexistent names, from a load event into a handful of cached
ranges. The module models the covered-range cache and measures
exactly that: how many upstream queries a flood of N distinct
nonexistent names costs with per-name negative caching versus
range caching, because the range approach only helps when the
gaps are wide, and a zone of tightly packed names sees little
benefit, which the report states rather than overselling the
technique as a universal shield.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class CoveredRange:
    low: str
    high: str

    def covers(self, name: str) -> bool:
        if self.low < self.high:
            return self.low < name < self.high
        return name > self.low or name < self.high


@dataclass
class AggressiveNegCache:
    ranges: list[CoveredRange] = field(default_factory=list)
    upstream_queries: int = 0
    range_hits: int = 0

    def learn_range(self, low: str, high: str) -> None:
        if low == high:
            raise Invalid(
                "a zero-width range covers nothing; that is a "
                "point, not a proof of absence"
            )
        self.ranges.append(CoveredRange(low=low, high=high))

    def query(self, name: str, gap_provider) -> str:
        for covered in self.ranges:
            if covered.covers(name):
                self.range_hits += 1
                return (
                    f"{name}: proven absent by a cached range "
                    f"({covered.low}..{covered.high}); no "
                    "upstream query"
                )
        low, high = gap_provider(name)
        self.learn_range(low, high)
        self.upstream_queries += 1
        return (
            f"{name}: absence fetched and the whole gap "
            f"{low}..{high} cached; the next name in it is "
            "free"
        )

    def flood_report(
        self, names: list[str], gap_provider
    ) -> str:
        if not names:
            raise Invalid("no flood to measure")
        for name in names:
            self.query(name, gap_provider)
        per_name_cost = len(names)
        saved = per_name_cost - self.upstream_queries
        return (
            f"{len(names)} nonexistent name(s): per-name "
            f"caching pays {per_name_cost} upstream queries, "
            f"range caching pays {self.upstream_queries}, "
            f"saving {saved}; the gain lives in wide gaps and "
            "a densely named zone would show less"
        )
