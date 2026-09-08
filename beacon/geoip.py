"""Geo-routing: answer with the nearest region, and admit the map is coarse.

Geo-aware DNS looks up the client's approximate location from
its address and answers with the nearest region's endpoint,
which is a real latency win and a bundle of half-truths worth
stating plainly. The location is the resolver's address, not
the user's, so a user on a public resolver in another country
is mapped to the resolver, and the module marks answers served
to known public-resolver ranges as low-confidence rather than
pretending precision it does not have. The distance is a
lookup table of region-to-region hops, not real network
latency, because DNS cannot measure the path it is choosing,
so the router picks nearest-by-table and says so. The fallback
is the part that saves the 3 a.m. page: when the nearest region
is unhealthy the router serves the next nearest, and a
geo-router with no health input would keep sending traffic to
the dead-but-close region, which is geo-routing optimizing the
one thing users do not care about, proximity to an outage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing

PUBLIC_RESOLVER_PREFIXES = ("8.8.", "1.1.", "9.9.")


@dataclass
class GeoRouter:
    region_of: dict[str, str] = field(default_factory=dict)
    distances: dict[tuple[str, str], int] = field(
        default_factory=dict
    )
    healthy_regions: set[str] = field(default_factory=set)

    def add_region(self, region: str) -> None:
        self.healthy_regions.add(region)

    def set_distance(
        self, a: str, b: str, hops: int
    ) -> None:
        if hops < 0:
            raise Invalid("distance cannot be negative")
        self.distances[(a, b)] = hops
        self.distances[(b, a)] = hops

    def locate(self, client_ip: str, region: str) -> None:
        self.region_of[client_ip] = region

    def _distance(self, a: str, b: str) -> int:
        if a == b:
            return 0
        return self.distances.get((a, b), 999)

    def route(self, client_ip: str) -> str:
        client_region = self.region_of.get(client_ip)
        if client_region is None:
            raise Missing(
                f"{client_ip} maps to no region; geo-routing "
                "without a location is a coin toss with extra "
                "steps"
            )
        healthy = sorted(self.healthy_regions)
        if not healthy:
            raise Missing("no healthy region to route to")
        nearest = min(
            healthy,
            key=lambda region: (
                self._distance(client_region, region),
                region,
            ),
        )
        confidence = (
            "low confidence"
            if client_ip.startswith(PUBLIC_RESOLVER_PREFIXES)
            else "confident"
        )
        note = ""
        if confidence == "low confidence":
            note = (
                "; the location is the public resolver's, not "
                "the user's"
            )
        return (
            f"{client_ip} -> {nearest} "
            f"({self._distance(client_region, nearest)} hops "
            f"by table, {confidence}){note}"
        )

    def mark_down(self, region: str) -> str:
        if region not in self.healthy_regions:
            raise Invalid(f"{region} was not healthy")
        self.healthy_regions.discard(region)
        return (
            f"{region} down: the router will serve the next "
            "nearest, because proximity to an outage is the "
            "one thing users do not care about"
        )
