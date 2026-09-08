"""Anycast: one address, many sites, and the routing table decides who answers.

Anycast advertises the same address from every site and lets
the network's own shortest-path routing send each client to
the nearest one, which is elegant until a site withdraws its
route and every client it served reroutes to the next-nearest
in a single convergence event. The model captures the two
properties operators actually plan around. Catchment: which
clients a site serves is decided by network distance, not by
the DNS, so a site's load is its catchment's size and the map
is the routing table, not a config file. Failover blast: when
a site withdraws, its whole catchment lands on neighbors at
once, and a neighbor already near capacity meets the shift as
a surge, so the planner computes the worst neighbor's post-
withdrawal load for each site and names the pair whose failure
would overload its backup, because anycast's failover is
automatic and therefore untested until it is real, and a
surge nobody modeled is a surge nobody provisioned for.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing


@dataclass
class AnycastFabric:
    sites: dict[str, int] = field(default_factory=dict)
    catchment: dict[str, str] = field(default_factory=dict)
    capacities: dict[str, int] = field(default_factory=dict)

    def add_site(self, name: str, capacity: int) -> None:
        if name in self.sites:
            raise Invalid(f"{name} already advertises")
        if capacity < 1:
            raise Invalid(f"{name} needs capacity to serve")
        self.sites[name] = 0
        self.capacities[name] = capacity

    def route_client(self, client: str, nearest_site: str) -> None:
        if nearest_site not in self.sites:
            raise Missing(f"{nearest_site} is not a site")
        old = self.catchment.get(client)
        if old is not None:
            self.sites[old] -= 1
        self.catchment[client] = nearest_site
        self.sites[nearest_site] += 1

    def withdraw(
        self, site: str, reroute: dict[str, str]
    ) -> str:
        if site not in self.sites:
            raise Missing(f"{site} is not advertising")
        orphaned = [
            client
            for client, home in self.catchment.items()
            if home == site
        ]
        for client in orphaned:
            target = reroute.get(client)
            if target is None or target not in self.sites:
                raise Invalid(
                    f"{client} has no next-nearest site in "
                    "the reroute map; the network would "
                    "blackhole it"
                )
            if target == site:
                raise Invalid(
                    f"{client} reroutes to the withdrawing "
                    "site; that is not a reroute"
                )
        self.sites[site] = 0
        del self.sites[site]
        del self.capacities[site]
        for client in orphaned:
            self.catchment[client] = reroute[client]
            self.sites[reroute[client]] += 1
        return (
            f"{site} withdrawn: {len(orphaned)} client(s) "
            "rerouted in one convergence event"
        )

    def surge_report(self, reroute: dict[str, str]) -> str:
        worst_site = ""
        worst_load = 0.0
        for site in self.sites:
            projected = dict(self.sites)
            for client, home in self.catchment.items():
                if home == site:
                    projected[reroute.get(client, site)] = (
                        projected.get(reroute.get(client, site), 0)
                        + 1
                    )
            for neighbor, load in projected.items():
                if neighbor == site:
                    continue
                ratio = load / self.capacities[neighbor]
                if ratio > worst_load:
                    worst_load = ratio
                    worst_site = f"{site} -> {neighbor}"
        return (
            f"the worst failover is {worst_site} at "
            f"{worst_load:.0%} of capacity; anycast failover "
            "is automatic and therefore untested until it is "
            "real"
        )
