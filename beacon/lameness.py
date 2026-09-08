"""Lame delegation: the parent points at a server that shrugs.

A delegation is a promise the parent makes on the child's
behalf, and a lame server is the promise broken: the NS record
says ask ns2, and ns2 answers without authority, refuses, or
has never heard of the zone. Resolvers meeting lameness pay
twice, once for the wasted query and once for the retry
elsewhere, so the tracker keeps a lameness score per
delegation edge and quarantines edges that fail repeatedly,
consulting them last instead of never, because servers get
fixed and a permanent blacklist turns yesterday's outage into
a permanent half-fleet. The census is for the zone operator:
every edge with its verdict, authoritative, lame, or
quarantined, and the classic finding named when it appears,
the delegation updated on the parent but never on the child,
which is how a nameserver ends up lame for a zone it served
faithfully last month.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

QUARANTINE_AFTER = 3


@dataclass
class EdgeHealth:
    server: str
    zone: str
    lame_count: int = 0
    authoritative_count: int = 0

    def quarantined(self) -> bool:
        return self.lame_count >= QUARANTINE_AFTER


@dataclass
class LamenessTracker:
    edges: dict[tuple[str, str], EdgeHealth] = field(
        default_factory=dict
    )
    wasted_queries: int = 0

    def _edge(self, zone: str, server: str) -> EdgeHealth:
        key = (zone, server)
        if key not in self.edges:
            self.edges[key] = EdgeHealth(
                server=server, zone=zone
            )
        return self.edges[key]

    def observe(
        self, zone: str, server: str, answered_with_authority: bool
    ) -> str:
        edge = self._edge(zone, server)
        if answered_with_authority:
            edge.authoritative_count += 1
            if edge.lame_count > 0:
                edge.lame_count = 0
                return (
                    f"{server} answered {zone} with authority; "
                    "the lameness score resets, because "
                    "servers get fixed"
                )
            return f"{server} authoritative for {zone}"
        edge.lame_count += 1
        self.wasted_queries += 1
        if edge.quarantined():
            return (
                f"{server} QUARANTINED for {zone} after "
                f"{edge.lame_count} shrugs: consulted last, "
                "not never, because a permanent blacklist "
                "turns yesterday's outage into a permanent "
                "half-fleet"
            )
        return (
            f"{server} lame for {zone} "
            f"({edge.lame_count}/{QUARANTINE_AFTER}); the "
            "parent's promise, broken by the child"
        )

    def consultation_order(
        self, zone: str, servers: list[str]
    ) -> list[str]:
        if not servers:
            raise Invalid("no servers to order")
        return sorted(
            servers,
            key=lambda server: (
                self._edge(zone, server).quarantined(),
                self._edge(zone, server).lame_count,
                server,
            ),
        )

    def census(self, zone: str) -> str:
        rows = [
            edge
            for (held_zone, _), edge in self.edges.items()
            if held_zone == zone
        ]
        if not rows:
            raise Invalid(f"no observations for {zone}")
        lines = [
            f"{zone}: {self.wasted_queries} wasted query(ies) "
            "paid to lameness"
        ]
        for edge in sorted(rows, key=lambda held: held.server):
            if edge.quarantined():
                verdict = "quarantined"
            elif edge.lame_count > 0:
                verdict = f"lame ({edge.lame_count})"
            else:
                verdict = "authoritative"
            lines.append(f"  {edge.server}: {verdict}")
        if any(
            edge.quarantined() and edge.authoritative_count > 0
            for edge in rows
        ):
            lines.append(
                "  a quarantined server that once answered "
                "with authority: the delegation moved on the "
                "parent but never on the child, the classic"
            )
        return "\n".join(lines)
