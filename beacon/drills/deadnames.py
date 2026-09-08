"""A morning of dead names prices the negative cache.

Monitoring probes a decommissioned host every tick, thirty
asks in the first negative-TTL window against a zone whose
negative TTL is 120. Without negative caching every ask
travels; with it, the first ask pays and the next twenty-nine
are answered from memory, so the window costs one upstream
query instead of thirty. The drill runs the same morning twice
through the real resolver and cache, and the second number
worth keeping is the expiry: at tick 120 the memory lapses,
exactly one more query travels, and the window starts again,
which is the negative TTL doing precisely what the SOA
promised, no more and no less. Twenty-nine saves per window
is the entire argument for caching a no as carefully as a
yes.
"""

from __future__ import annotations

import contextlib

from beacon.drills.finding import Finding
from beacon.errors import Missing
from beacon.names import Name
from beacon.records import Record
from beacon.resolver import Resolver
from beacon.zone import Soa, Zone

SOA = Soa(
    serial=1,
    refresh=3600,
    retry=600,
    expire=86400,
    negative_ttl=120,
)


def _fresh_resolver() -> Resolver:
    zone = Zone(apex=Name.parse("example.com"), soa=SOA)
    zone.add(
        Record(
            name=Name.parse("www.example.com"),
            rtype="A",
            value="192.0.2.10",
            ttl=300,
        )
    )
    resolver = Resolver()
    resolver.host_zone(zone)
    return resolver


def run() -> Finding:
    resolver = _fresh_resolver()
    ghost = Name.parse("decommissioned.example.com")
    for tick in range(0, 120, 4):
        with contextlib.suppress(Missing):
            resolver.resolve(ghost, "A", now=tick)
    first_window_queries = resolver.upstream_total
    with contextlib.suppress(Missing):
        resolver.resolve(ghost, "A", now=120)
    after_expiry_queries = resolver.upstream_total
    numbers = {
        "asks_in_window": 30,
        "upstream_first_window": first_window_queries,
        "negative_saves": resolver.cache.negative_saves,
        "upstream_after_expiry": after_expiry_queries,
        "naive_cost": 30,
    }
    holds = (
        numbers["upstream_first_window"] == 1
        and numbers["negative_saves"] == 29
        and numbers["upstream_after_expiry"] == 2
    )
    return Finding(
        drill="deadnames",
        claim=(
            "thirty asks about a dead name cost one upstream "
            "query; twenty-nine are answered from remembered "
            "no, and the lapse at tick 120 costs exactly one "
            "more, which is the SOA's promise kept to the tick"
        ),
        numbers=numbers,
        holds=holds,
    )
