"""TTL disobedience: the failover worked, and the pinned clients missed it.

The TTL is a contract most clients honor and some quietly do
not: connection pools that cache a resolved address for the
process lifetime, runtimes with their own resolver cache set
to forever, load balancers that resolve at config load and
never again. When traffic fails over by DNS, the obedient
population follows within one TTL and the disobedient keep
hammering the old address until someone restarts them, and
this module measures the wound: given the population mix and
the TTL, it charts traffic still arriving at the dead address
tick by tick, obedient traffic decaying to zero on schedule
while the pinned remainder holds as a floor that no DNS
change can lower. The floor is the finding, because teams
discover their disobedient fraction during their first real
failover, which is the most expensive possible classroom,
and this chart is the same lesson at desk prices.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class PopulationMix:
    obedient: int
    pinned: int
    ttl: int

    def __post_init__(self) -> None:
        if self.obedient < 0 or self.pinned < 0:
            raise Invalid("populations cannot be negative")
        if self.obedient + self.pinned == 0:
            raise Invalid("an empty population fails over trivially")
        if self.ttl < 1:
            raise Invalid("a ttl under one is not a contract")

    def traffic_at_dead_address(self, tick: int) -> int:
        if tick < 0:
            raise Invalid("time starts at the failover")
        if tick >= self.ttl:
            obedient_left = 0
        else:
            obedient_left = self.obedient * (
                self.ttl - tick
            ) // self.ttl
        return obedient_left + self.pinned

    def chart(self, ticks: int) -> list[int]:
        return [
            self.traffic_at_dead_address(tick)
            for tick in range(ticks)
        ]

    def floor_finding(self) -> str:
        total = self.obedient + self.pinned
        share = 100 * self.pinned // total
        if self.pinned == 0:
            return (
                f"all {total} client(s) obey the TTL; the "
                "dead address empties on schedule"
            )
        return (
            f"{self.pinned} of {total} client(s) ({share}%) "
            f"are pinned: after tick {self.ttl} the dead "
            "address still receives them, a floor no DNS "
            "change can lower, and teams usually learn this "
            "number during their first real failover, the "
            "most expensive possible classroom"
        )
