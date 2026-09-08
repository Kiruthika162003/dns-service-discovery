"""Load shedding by priority: drop the cheap work first to save the vital.

An overloaded server that sheds requests at random treats a
health check, a control-plane update, and a speculative prefetch
as equals, which means at the worst possible moment it may drop
the very traffic that would let it recover while admitting work
that does not matter. Priority load shedding reserves the top of
the server's capacity for the requests that matter most: each
priority is admitted only while in-flight work sits below a
cutoff scaled to that priority, so low-priority requests are
refused first as load climbs and critical requests keep being
admitted almost to the ceiling. The effect is that as the server
saturates it sheds a graceful gradient, prefetches first, then
normal traffic, then high, and only at the very edge does it
touch the critical control plane. The module maps each priority
to its cutoff and answers admit-or-shed for a given in-flight
level, so the order in which work is sacrificed is a policy set in
advance, not an accident of which request happened to arrive
during the spike.
"""

from __future__ import annotations

from beacon.errors import Invalid

PRIORITY_CUTOFF = {
    "critical": 1.0,
    "high": 0.8,
    "normal": 0.5,
    "low": 0.2,
}


class LoadShedder:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise Invalid(
                "a capacity of zero admits nothing at any "
                "priority; that is an outage, not shedding"
            )
        self.capacity = capacity

    def cutoff(self, priority: str) -> float:
        if priority not in PRIORITY_CUTOFF:
            raise Invalid(
                f"{priority!r} is not a known priority; it knows "
                f"{', '.join(PRIORITY_CUTOFF)}"
            )
        return self.capacity * PRIORITY_CUTOFF[priority]

    def admit(self, inflight: int, priority: str) -> bool:
        return inflight < self.cutoff(priority)

    def shed_order(self, inflight: int) -> list[str]:
        return [
            priority
            for priority in ("low", "normal", "high", "critical")
            if not self.admit(inflight, priority)
        ]
