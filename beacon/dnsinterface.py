"""Serving the registry over DNS: SRV answers with a TTL chosen on purpose.

Every service mesh eventually meets the client that speaks
nothing but DNS, and the bridge synthesizes SRV records from
live registry state: one record per passing instance,
priority flat, weight carried over, port from the
registration. The decision that matters is the TTL, because
it is the staleness budget handed to every cache between here
and the caller: too long and a deregistered instance keeps
receiving connections for the whole window, too short and the
bridge becomes the hot path for every connection setup. The
chooser makes the tradeoff explicit from the service's churn,
stable services earn longer TTLs, churny ones get short, and
the mismatch report prices yesterday's choice against
yesterday's churn, naming the connections that a too-long TTL
sent to the dead, which is the cost column TTL debates
usually argue without.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing

STABLE_TTL = 60
CHURNY_TTL = 5
CHURN_THRESHOLD = 3


@dataclass
class BridgeRecord:
    service: str
    target: str
    port: int
    weight: int
    ttl: int

    def line(self) -> str:
        return (
            f"_svc._tcp.{self.service}. {self.ttl} SRV 10 "
            f"{self.weight} {self.port} {self.target}"
        )


@dataclass
class DnsBridge:
    churn_by_service: dict[str, int] = field(
        default_factory=dict
    )
    sent_to_the_dead: int = 0

    def note_churn(self, service: str, events: int) -> None:
        if events < 0:
            raise Invalid("churn cannot be negative")
        self.churn_by_service[service] = events

    def ttl_for(self, service: str) -> int:
        churn = self.churn_by_service.get(service, 0)
        if churn >= CHURN_THRESHOLD:
            return CHURNY_TTL
        return STABLE_TTL

    def synthesize(
        self,
        service: str,
        instances: list[tuple[str, int, int, bool]],
    ) -> list[BridgeRecord]:
        passing = [
            (target, port, weight)
            for target, port, weight, healthy in instances
            if healthy
        ]
        if not passing:
            raise Missing(
                f"{service} has nobody passing; synthesizing "
                "an empty SRV set would cache the absence"
            )
        ttl = self.ttl_for(service)
        return [
            BridgeRecord(
                service=service,
                target=target,
                port=port,
                weight=weight,
                ttl=ttl,
            )
            for target, port, weight in sorted(passing)
        ]

    def mismatch_report(
        self,
        service: str,
        ttl_used: int,
        deregistrations: int,
        connections_per_tick: int,
    ) -> str:
        if connections_per_tick < 0:
            raise Invalid("connection rates cannot be negative")
        exposure = (
            deregistrations
            * ttl_used
            * connections_per_tick
            // 2
        )
        self.sent_to_the_dead += exposure
        right_ttl = self.ttl_for(service)
        line = (
            f"{service}: ttl {ttl_used} against "
            f"{deregistrations} deregistration(s) sent "
            f"roughly {exposure} connection(s) to the dead"
        )
        if ttl_used > right_ttl:
            line += (
                f"; churn says {right_ttl} was the honest "
                "choice, and this is the cost column TTL "
                "debates argue without"
            )
        return line
