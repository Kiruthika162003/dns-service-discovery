"""Panic mode: when too few hosts are healthy, stop trusting the health checks.

A load balancer normally routes only to hosts that pass their
health checks, which is right until it is catastrophically
wrong. If a bad deploy or a network partition marks eighty
percent of a pool unhealthy, routing all traffic to the
surviving twenty percent guarantees they overload and fail too,
and the health checks that were trying to protect the pool
instead drive it off a cliff. Panic mode is the deliberate loss
of nerve that prevents this: once the healthy fraction drops
below a threshold, the balancer concludes the health signal is
more likely systemically broken than the hosts, and it routes to
every host, healthy or not, spreading the load rather than
concentrating it. The logic is counterintuitive and that is why
it must be explicit: when things look worst, the safest move is
to stop being selective, because a request sent to a maybe-dead
host that might answer beats piling onto a live host until it
dies for certain. The module names the threshold and the pool it
returns so an operator can see when the balancer gave up
filtering and why.
"""

from __future__ import annotations

from beacon.errors import Invalid


class PanicPolicy:
    def __init__(self, threshold: float = 0.5) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise Invalid(
                f"a panic threshold of {threshold} is not a "
                "fraction; it is the share of healthy hosts below "
                "which filtering stops"
            )
        self.threshold = threshold

    def healthy_fraction(self, healthy: int, total: int) -> float:
        if total <= 0:
            raise Invalid(
                "a pool of zero hosts has no fraction healthy; "
                "there is nothing to route to at all"
            )
        return healthy / total

    def in_panic(self, healthy: int, total: int) -> bool:
        return self.healthy_fraction(healthy, total) < self.threshold

    def route_pool(
        self, healthy_hosts: list[str], all_hosts: list[str]
    ) -> list[str]:
        if self.in_panic(len(healthy_hosts), len(all_hosts)):
            return list(all_hosts)
        return list(healthy_hosts)

    def explain(self, healthy: int, total: int) -> str:
        fraction = self.healthy_fraction(healthy, total)
        if fraction < self.threshold:
            return (
                f"panic: {fraction:.0%} healthy is below the "
                f"{self.threshold:.0%} threshold, so filtering "
                "stops and every host takes traffic to avoid "
                "overloading the survivors into failure"
            )
        return (
            f"normal: {fraction:.0%} healthy is above the "
            f"{self.threshold:.0%} threshold; only healthy hosts "
            "take traffic"
        )
