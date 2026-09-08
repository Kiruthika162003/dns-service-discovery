"""Alias chains: convenient hops that quietly add latency and single points.

A CNAME points a name at another name, and chains form
naturally: the vanity domain aliases the load balancer aliases
the cloud endpoint aliases the region. Each hop is one more
lookup on the critical path and one more thing that can break,
and the danger is that no single team sees the whole chain, so
it grows one convenient hop at a time until a four-hop chain
adds four cache misses to a cold resolution. The analyzer walks
a chain to its terminal address, counts the hops, prices the
cold-resolution latency at one round trip per uncached hop, and
names the two failure shapes that hide in chains: the loop,
where a hop eventually points back into the chain, caught
rather than followed forever, and the dangling end, where the
last CNAME points at a name that resolves to nothing, an
outage that the chain's length delayed anyone from noticing.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid, Loop, Missing

ROUND_TRIP = 25
CHAIN_ALARM = 3


@dataclass
class ChainResult:
    hops: list[str]
    terminal: str
    cold_latency: int


def follow_chain(
    start: str,
    cnames: dict[str, str],
    addresses: dict[str, str],
) -> ChainResult:
    hops = []
    seen = set()
    current = start
    while current in cnames:
        if current in seen:
            raise Loop(
                f"the chain from {start} loops at {current}; "
                "an alias pointing back into its own chain is "
                "caught, not followed forever"
            )
        seen.add(current)
        hops.append(current)
        current = cnames[current]
        if len(hops) > 32:
            raise Loop("the chain is absurdly long")
    if current not in addresses:
        raise Missing(
            f"the chain from {start} ends at {current}, which "
            "resolves to nothing; a dangling end is an outage "
            "the chain's length delayed anyone from noticing"
        )
    return ChainResult(
        hops=hops,
        terminal=addresses[current],
        cold_latency=(len(hops) + 1) * ROUND_TRIP,
    )


def chain_report(
    start: str,
    cnames: dict[str, str],
    addresses: dict[str, str],
) -> str:
    result = follow_chain(start, cnames, addresses)
    hop_count = len(result.hops)
    line = (
        f"{start} -> {result.terminal} in {hop_count} hop(s); "
        f"cold latency {result.cold_latency} tick(s)"
    )
    if hop_count >= CHAIN_ALARM:
        line += (
            f"; {hop_count} hops each add a cache miss to a "
            "cold resolution, and no single team sees the "
            "whole chain, which is how it grew"
        )
    return line


def flatten_suggestion(
    start: str,
    cnames: dict[str, str],
    addresses: dict[str, str],
) -> str:
    result = follow_chain(start, cnames, addresses)
    if len(result.hops) <= 1:
        raise Invalid(
            f"{start} is already short; flattening a one-hop "
            "alias trades clarity for nothing"
        )
    saved = len(result.hops) * ROUND_TRIP
    return (
        f"point {start} straight at {result.terminal}: "
        f"collapses {len(result.hops)} hop(s) and saves "
        f"{saved} cold tick(s), at the cost of the "
        "indirection each hop was bought to buy"
    )
