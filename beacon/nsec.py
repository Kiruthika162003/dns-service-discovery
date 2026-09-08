"""Authenticated denial: proving a name does not exist without listing them all.

A signed zone must prove NXDOMAIN as rigorously as it proves a
record, and it cannot sign every nonexistent name because
there are infinitely many. NSEC chains the existing names in
canonical order and signs the gaps: a record saying nothing
exists between alpha and gamma proves beta absent by covering
the interval where beta would sort. The property this module
keeps honest is the leak: NSEC's proof reveals the names on
either side of the gap, so anyone can walk the whole chain by
asking for successive nonexistent names, and a zone that
thought its private names were hidden by their unpredictability
learns they were enumerable all along. NSEC3 hashes the names
before chaining, proving denial over the hashes so the gaps
reveal digests instead of names, and the module measures the
tradeoff the two make with the same zone: walk resistance
against the cost of hashing every query, because the choice
between them is a real one and the leak is the reason it
exists.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class NsecZone:
    names: list[str] = field(default_factory=list)

    def add(self, name: str) -> None:
        if name in self.names:
            raise Invalid(f"{name} already in the zone")
        self.names.append(name)
        self.names.sort()

    def prove_absence(self, query: str) -> str:
        if query in self.names:
            raise Invalid(
                f"{query} exists; NSEC proves absence, not "
                "presence"
            )
        if not self.names:
            raise Invalid("an empty zone has no chain to prove with")
        low = None
        high = None
        for name in self.names:
            if name < query:
                low = name
            elif high is None:
                high = name
        low = low if low is not None else self.names[-1]
        high = high if high is not None else self.names[0]
        return (
            f"nothing exists between {low} and {high}; {query} "
            "would sort there and does not, proven, and the "
            "two boundary names just leaked"
        )

    def zone_walk(self) -> list[str]:
        return list(self.names)


def nsec3_hash(name: str, iterations: int) -> str:
    digest = name.encode()
    for _ in range(iterations + 1):
        digest = hashlib.sha256(digest).digest()
    return digest.hex()[:12]


def tradeoff_report(
    zone: NsecZone, iterations: int
) -> str:
    if not zone.names:
        raise Invalid("no zone to compare")
    nsec_leak = len(zone.zone_walk())
    hashed = sorted(
        nsec3_hash(name, iterations) for name in zone.names
    )
    return (
        f"NSEC leaks all {nsec_leak} name(s) to a zone walk; "
        f"NSEC3 leaks {len(hashed)} hash(es) instead, at the "
        f"cost of {iterations + 1} hash round(s) per query, "
        "and this is the choice the leak exists to force"
    )
