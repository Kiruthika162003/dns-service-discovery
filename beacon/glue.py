"""Glue records: the referral must carry the address it points at.

Delegation has a chicken-and-egg baked in: example.com
delegates eu.example.com to ns1.eu.example.com, and a resolver
following that referral must resolve ns1.eu.example.com, which
lives inside the very zone it is trying to reach. Without help
the descent deadlocks politely forever. Glue is the help: when
a delegation's nameserver lives at or below the delegation
point, the parent must publish the nameserver's address
alongside the NS record, not as authoritative data but as a
courtesy the descent cannot proceed without. The checker
audits every delegation for exactly this: in-bailiwick
nameservers without glue are named as deadlocks, out-of-zone
nameservers are fine without it because the resolver can reach
them independently, and unnecessary glue, addresses for
nameservers that live elsewhere, is flagged too, because stale
courtesy answers are how a moved nameserver keeps receiving
traffic at its old house for a year.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid
from beacon.names import Name


@dataclass
class Delegation:
    cut: Name
    nameservers: list[Name] = field(default_factory=list)
    glue: dict[str, str] = field(default_factory=dict)


@dataclass
class GlueAuditor:
    apex: Name
    delegations: list[Delegation] = field(default_factory=list)

    def delegate(
        self,
        cut: str,
        nameservers: list[str],
        glue: dict[str, str] | None = None,
    ) -> None:
        cut_name = Name.parse(cut)
        if not cut_name.is_subdomain_of(self.apex):
            raise Invalid(
                f"{cut} is not under {self.apex.canonical()}; "
                "one delegates only what one holds"
            )
        self.delegations.append(
            Delegation(
                cut=cut_name,
                nameservers=[
                    Name.parse(ns) for ns in nameservers
                ],
                glue=dict(glue or {}),
            )
        )

    def audit(self) -> str:
        deadlocks = []
        stale_courtesy = []
        healthy = 0
        for delegation in self.delegations:
            for ns in delegation.nameservers:
                in_bailiwick = ns.is_subdomain_of(
                    delegation.cut
                )
                has_glue = ns.canonical() in delegation.glue
                if in_bailiwick and not has_glue:
                    deadlocks.append(
                        f"{delegation.cut.canonical()} -> "
                        f"{ns.canonical()}: the nameserver "
                        "lives inside the zone it serves and "
                        "no glue carries its address; the "
                        "descent deadlocks politely forever"
                    )
                elif not in_bailiwick and has_glue:
                    stale_courtesy.append(
                        f"{delegation.cut.canonical()} -> "
                        f"{ns.canonical()}: glue for a "
                        "nameserver that lives elsewhere; "
                        "stale courtesy is how a moved server "
                        "receives traffic at its old house"
                    )
                else:
                    healthy += 1
        lines = [
            f"{healthy} delegation edge(s) healthy, "
            f"{len(deadlocks)} deadlock(s), "
            f"{len(stale_courtesy)} stale courtesy record(s)"
        ]
        lines.extend(f"  {entry}" for entry in deadlocks)
        lines.extend(f"  {entry}" for entry in stale_courtesy)
        return "\n".join(lines)
