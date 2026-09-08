"""Replica spread: three copies in one rack is one copy with confidence.

A service running three replicas has bought fault tolerance
only if the replicas cannot die together, and the spread
checker prices exactly that: replicas are placed in fault
domains, racks or zones, and the report computes the blast of
each domain's failure, the largest fraction of any service
lost to a single domain going dark. The number that matters is
worst-case survivors: a service with replicas spread two and
one loses at most two to one domain and keeps serving, while
three-in-one-rack loses everything to a power supply, and the
checker calls that placement what it is, one copy wearing
three copies' cost. The rebalance suggestion is concrete,
which replica to move and where, chosen to minimize movement,
because "spread your replicas" is advice while "move
billing-3 from rack-a to rack-c" is a change request.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class SpreadChecker:
    placements: dict[str, dict[str, str]] = field(
        default_factory=dict
    )

    def place(
        self, service: str, replica: str, domain: str
    ) -> None:
        held = self.placements.setdefault(service, {})
        if replica in held:
            raise Invalid(
                f"{replica} is already placed in {held[replica]}"
            )
        held[replica] = domain

    def _by_domain(self, service: str) -> dict[str, list[str]]:
        held = self.placements.get(service)
        if not held:
            raise Invalid(f"{service} has no placements")
        grouped: dict[str, list[str]] = {}
        for replica, domain in held.items():
            grouped.setdefault(domain, []).append(replica)
        return grouped

    def worst_blast(self, service: str) -> tuple[str, int, int]:
        grouped = self._by_domain(service)
        total = sum(len(v) for v in grouped.values())
        domain, lost = max(
            grouped.items(), key=lambda row: (len(row[1]), row[0])
        )
        return domain, len(lost), total - len(lost)

    def verdict(self, service: str) -> str:
        domain, lost, survivors = self.worst_blast(service)
        if survivors == 0:
            return (
                f"{service}: {lost} replica(s) all in "
                f"{domain}; one copy wearing "
                f"{lost} copies' cost, and one power supply "
                "away from zero"
            )
        return (
            f"{service}: worst domain {domain} takes {lost}, "
            f"{survivors} survive and keep serving"
        )

    def known_domains(self) -> list[str]:
        found = {
            domain
            for held in self.placements.values()
            for domain in held.values()
        }
        return sorted(found)

    def rebalance_suggestion(self, service: str) -> str:
        grouped = self._by_domain(service)
        domains = self.known_domains()
        counts = {
            name: len(grouped.get(name, ())) for name in domains
        }
        heaviest = max(
            domains, key=lambda name: (counts[name], name)
        )
        lightest = min(
            domains, key=lambda name: (counts[name], name)
        )
        if counts[heaviest] - counts[lightest] <= 1:
            return (
                f"{service}: the spread is within one; moving "
                "anything buys nothing"
            )
        replica = sorted(grouped[heaviest])[-1]
        return (
            f"{service}: move {replica} from {heaviest} to "
            f"{lightest}; one move, because spread-your-"
            "replicas is advice and this is a change request"
        )
