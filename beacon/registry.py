"""The service registry: an instance is an address plus a promise to answer.

Discovery differs from DNS in one temperament: DNS records are
declarations, registry entries are claims that decay. An
instance registers with an address, a port, and a lease; it
must renew before the lease runs out or the registry stops
vouching for it, because an entry nobody renews describes a
process that may have died mid-request, and serving it is how
load balancers learn to send traffic to ghosts. Health is a
separate axis from liveness: a leased instance can be marked
failing by its checks and stays registered but undandled,
visible to operators and invisible to callers, since the
alternative, deregistering the sick, erases exactly the
evidence the operator needs. Queries answer only with leased,
passing instances, and the registry says plainly when a
service exists but has nobody fit to answer, because an empty
answer with a reason beats an empty answer that looks like a
typo in the service name.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing

DEFAULT_LEASE = 30


@dataclass
class Instance:
    instance_id: str
    address: str
    port: int
    leased_until: int
    healthy: bool = True

    def alive(self, now: int) -> bool:
        return now < self.leased_until


@dataclass
class Registry:
    services: dict[str, dict[str, Instance]] = field(
        default_factory=dict
    )
    ghosts_refused: int = 0

    def register(
        self,
        service: str,
        instance_id: str,
        address: str,
        port: int,
        now: int,
        lease: int = DEFAULT_LEASE,
    ) -> str:
        if not 1 <= port <= 65_535:
            raise Invalid(f"port {port} is not a port")
        if lease < 1:
            raise Invalid(
                "a lease under one tick is a registration "
                "that expires before it lands"
            )
        held = self.services.setdefault(service, {})
        held[instance_id] = Instance(
            instance_id=instance_id,
            address=address,
            port=port,
            leased_until=now + lease,
        )
        return (
            f"{instance_id} vouched for until {now + lease}; "
            "renew or the vouching stops"
        )

    def renew(
        self, service: str, instance_id: str, now: int,
        lease: int = DEFAULT_LEASE,
    ) -> str:
        instance = self._find(service, instance_id)
        if not instance.alive(now):
            raise Missing(
                f"{instance_id} let its lease lapse at "
                f"{instance.leased_until}; a lapsed instance "
                "re-registers, it does not renew, because the "
                "gap is exactly the interval nobody vouched for"
            )
        instance.leased_until = now + lease
        return f"{instance_id} renewed until {now + lease}"

    def report_health(
        self, service: str, instance_id: str, passing: bool
    ) -> str:
        instance = self._find(service, instance_id)
        instance.healthy = passing
        if passing:
            return f"{instance_id} passing"
        return (
            f"{instance_id} failing: registered but unserved, "
            "visible to operators and invisible to callers"
        )

    def _find(self, service: str, instance_id: str) -> Instance:
        held = self.services.get(service, {})
        instance = held.get(instance_id)
        if instance is None:
            raise Missing(
                f"{instance_id} is not registered under "
                f"{service}"
            )
        return instance

    def discover(self, service: str, now: int) -> list[Instance]:
        held = self.services.get(service)
        if held is None:
            raise Missing(
                f"no service named {service} was ever "
                "registered; an empty answer with a reason "
                "beats one that looks like a typo"
            )
        alive = []
        for instance in held.values():
            if not instance.alive(now):
                self.ghosts_refused += 1
                continue
            if instance.healthy:
                alive.append(instance)
        if not alive:
            raise Missing(
                f"{service} exists but has nobody fit to "
                "answer: every instance is lapsed or failing"
            )
        return sorted(alive, key=lambda held: held.instance_id)

    def census(self, service: str, now: int) -> str:
        held = self.services.get(service, {})
        leased = sum(
            1 for i in held.values() if i.alive(now)
        )
        failing = sum(
            1
            for i in held.values()
            if i.alive(now) and not i.healthy
        )
        lapsed = len(held) - leased
        return (
            f"{service}: {leased} leased ({failing} failing), "
            f"{lapsed} lapsed, {self.ghosts_refused} ghost "
            "serve(s) refused so far"
        )
