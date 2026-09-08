"""Registration leases: a service is alive only as long as its heartbeat is fresh.

A service registry that kept an instance forever once registered
would fill with the ghosts of crashed processes that never got to
deregister, so registration is a lease, not a deed: an instance
holds its slot for a time-to-live and must heartbeat to renew it,
and a sweep expires any lease whose last heartbeat has aged past
the ttl. The subtle rule is the relationship between the heartbeat
interval and the ttl. If the interval is not comfortably shorter
than the ttl, a single lost heartbeat, one dropped packet, expires
a perfectly healthy instance, and the registry flaps its members
on ordinary network jitter. The safe ratio is a heartbeat at least
twice as often as the ttl, so it takes two consecutive misses, not
one, to drop an instance, and the module refuses to accept a
heartbeat interval that does not clear that bar, because a lease
that expires on one lost packet is worse than no lease at all: it
adds churn without adding safety.
"""

from __future__ import annotations

from beacon.errors import Invalid


class LeaseRegistry:
    def __init__(self, ttl: int, heartbeat_interval: int) -> None:
        if ttl <= 0:
            raise Invalid("a lease ttl must be positive")
        if heartbeat_interval * 2 > ttl:
            raise Invalid(
                f"a {heartbeat_interval}s heartbeat against a "
                f"{ttl}s ttl expires an instance on a single lost "
                "packet; heartbeat at least twice as often so two "
                "misses, not one, are needed to drop it"
            )
        self.ttl = ttl
        self.last_seen: dict[str, int] = {}

    def register(self, name: str, now: int) -> None:
        self.last_seen[name] = now

    def heartbeat(self, name: str, now: int) -> None:
        if name not in self.last_seen:
            raise Invalid(
                f"{name} has no lease to renew; a heartbeat for an "
                "unregistered instance must register first, not "
                "silently resurrect a swept ghost"
            )
        self.last_seen[name] = now

    def alive(self, name: str, now: int) -> bool:
        seen = self.last_seen.get(name)
        return seen is not None and now - seen <= self.ttl

    def sweep(self, now: int) -> list[str]:
        expired = [
            name
            for name, seen in self.last_seen.items()
            if now - seen > self.ttl
        ]
        for name in expired:
            del self.last_seen[name]
        return sorted(expired)
