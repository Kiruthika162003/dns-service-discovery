"""The rebind guard: outside names do not get to point inside the house.

DNS rebinding is a browser attack wearing a resolver's
uniform: a hostile external domain first answers with its own
public address, then flips the record to 10.0.0.5, and the
victim's browser, still trusting the same origin, happily
speaks to the internal service with the attacker's script at
the wheel. The guard is a policy at the cache door: answers
arriving from external resolution whose addresses land in
private, loopback, or link-local space are refused, logged,
and never cached, because there is no honest reason for a
public domain to resolve to the inside of this particular
building. The carve-out list exists for the legitimate cases,
split-horizon names the operator declares on purpose, and it
is exact-match and audited, since a wildcarded exception to a
security rule is the rule resigning with a notice period.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Refused

PRIVATE_PREFIXES = (
    "10.",
    "192.168.",
    "127.",
    "169.254.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.2",
    "172.30.",
    "172.31.",
)


def lands_inside(address: str) -> bool:
    return address.startswith(PRIVATE_PREFIXES)


@dataclass
class RebindGuard:
    allowed_names: set[str] = field(default_factory=set)
    refusals: list[str] = field(default_factory=list)

    def allow(self, name: str) -> None:
        if "*" in name:
            raise Invalid(
                "a wildcarded exception to a security rule is "
                "the rule resigning with a notice period"
            )
        self.allowed_names.add(name)

    def admit(
        self, name: str, address: str, now: int
    ) -> str:
        if not lands_inside(address):
            return f"{name} -> {address}: outside stays outside"
        if name in self.allowed_names:
            return (
                f"{name} -> {address}: inside by declared "
                "carve-out, exact-match and audited"
            )
        refusal = (
            f"[{now}] {name} -> {address} REFUSED: a public "
            "domain has no honest reason to resolve to the "
            "inside of this building"
        )
        self.refusals.append(refusal)
        raise Refused(refusal)

    def audit_page(self) -> str:
        lines = [
            f"{len(self.allowed_names)} carve-out(s), "
            f"{len(self.refusals)} rebind refusal(s)"
        ]
        for name in sorted(self.allowed_names):
            lines.append(f"  allowed: {name}")
        lines.extend(
            f"  {entry}" for entry in self.refusals[-3:]
        )
        return "\n".join(lines)
