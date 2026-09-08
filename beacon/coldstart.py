"""Cold cache economics: the empty resolver is a thundering herd waiting to fire.

A resolver restart empties the cache, and the first request for
each popular name misses and travels upstream, so a restart
under load sends a burst of upstream queries proportional to
the working set, all at once, which can overwhelm an authority
that comfortably served the steady state. The model prices the
cold-start burst against the warm steady state and shows the
two mitigations honestly. Cache persistence: writing the cache
to disk before restart and reloading it skips the burst
entirely, at the cost of possibly serving entries that expired
during downtime, which the module bounds by refusing to reload
entries older than their TTL. Staggered restart: bringing
resolvers back one at a time so the herd is spread over
minutes rather than fired in one instant, which trades total
recovery time for a survivable burst. The report contrasts
all three so the operator sees that the fastest restart is the
one most likely to take the authority down with it.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class ColdStartModel:
    working_set: int
    warm_miss_rate: float
    authority_capacity: int

    def __post_init__(self) -> None:
        if self.working_set < 1:
            raise Invalid("an empty working set has no burst")
        if not 0 <= self.warm_miss_rate <= 1:
            raise Invalid("the miss rate is a fraction")
        if self.authority_capacity < 1:
            raise Invalid("the authority must serve something")

    def cold_burst(self) -> int:
        return self.working_set

    def warm_load(self) -> int:
        return round(self.working_set * self.warm_miss_rate)

    def cold_overwhelms(self) -> bool:
        return self.cold_burst() > self.authority_capacity

    def staggered_peak(self, waves: int) -> int:
        if waves < 1:
            raise Invalid("a restart happens in at least one wave")
        return -(-self.working_set // waves)

    def strategy_report(self, waves: int) -> str:
        cold = self.cold_burst()
        warm = self.warm_load()
        staggered = self.staggered_peak(waves)
        lines = [
            f"working set {self.working_set}: cold burst "
            f"{cold}, warm load {warm}, authority capacity "
            f"{self.authority_capacity}"
        ]
        if self.cold_overwhelms():
            lines.append(
                f"  the naive restart's {cold}-query burst "
                "exceeds capacity; the fastest restart takes "
                "the authority down with it"
            )
        lines.append(
            "  persistence: reload skips the burst, bounded "
            "by refusing entries past their ttl"
        )
        lines.append(
            f"  staggered over {waves} wave(s): peak "
            f"{staggered}, "
            f"{'survivable' if staggered <= self.authority_capacity else 'still over'}"
        )
        return "\n".join(lines)


def reloadable(age: int, ttl: int) -> bool:
    if ttl < 0:
        raise Invalid("a negative ttl is not a lifespan")
    return age < ttl
