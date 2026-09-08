"""Forwarding: the resolver that delegates its curiosity, with a fallback vote.

Sites put a forwarder between themselves and the internet for
caching, policy, or the firewall's comfort, and the two modes
differ in one temperament. Forward-only trusts the forwarder
completely: if it fails, resolution fails, which is honest
when the firewall makes direct queries impossible anyway.
Forward-first tries the forwarder and falls back to full
recursion on failure, which sounds strictly better and hides
a trap this module names: a forwarder that answers slowly but
successfully never triggers the fallback, so the site's
resolution speed is hostage to the forwarder's worst day
while the fallback path quietly atrophies untested. The
ledger therefore tracks fallback exercises separately from
failures, and the health verdict flags a forward-first setup
whose fallback has never once run, because an escape hatch
that has never opened is a wall with a handle painted on.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid, Refused


@dataclass
class ForwarderPolicy:
    mode: str
    forwarder_queries: int = 0
    forwarder_failures: int = 0
    fallback_exercises: int = 0
    hostage_ticks: int = 0

    def __post_init__(self) -> None:
        if self.mode not in ("forward-only", "forward-first"):
            raise Invalid(
                f"{self.mode} is not a forwarding mode; "
                "forward-only or forward-first"
            )

    def resolve(
        self,
        forwarder_up: bool,
        forwarder_latency: int,
        direct_latency: int,
    ) -> str:
        self.forwarder_queries += 1
        if forwarder_up:
            if forwarder_latency > direct_latency:
                self.hostage_ticks += (
                    forwarder_latency - direct_latency
                )
            return (
                f"answered via forwarder in "
                f"{forwarder_latency} tick(s)"
            )
        self.forwarder_failures += 1
        if self.mode == "forward-only":
            raise Refused(
                "the forwarder is down and forward-only "
                "means what it says; honest, when the "
                "firewall makes direct queries impossible "
                "anyway"
            )
        self.fallback_exercises += 1
        return (
            f"forwarder down; fell back to full recursion in "
            f"{direct_latency} tick(s), and the escape hatch "
            "proved it opens"
        )

    def health_verdict(self) -> str:
        if self.mode == "forward-only":
            return (
                f"forward-only: {self.forwarder_failures} "
                f"failure(s) were {self.forwarder_failures} "
                "refusal(s); the trust is total and declared"
            )
        if self.fallback_exercises == 0:
            return (
                f"forward-first with {self.forwarder_queries} "
                "query(ies) and a fallback that has never "
                "once run: an escape hatch that has never "
                "opened is a wall with a handle painted on"
            )
        return (
            f"forward-first: fallback exercised "
            f"{self.fallback_exercises} time(s), "
            f"{self.hostage_ticks} tick(s) spent hostage to "
            "the forwarder's slow days that never triggered it"
        )
