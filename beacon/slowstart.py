"""Slow start: ramp a freshly healthy backend up, because full traffic on a cold one flaps.

A backend that just passed its health check is healthy but not
yet warm: its caches are empty, its connection pools unfilled,
its runtime not yet optimized, and slamming it with a full share
of traffic the instant it goes healthy spikes its latency, which
trips the very health check that just cleared it, which pulls the
traffic away, which lets it recover, which passes the check
again, and the backend flaps in and out while serving badly the
whole time. Slow start breaks the loop by ramping the backend's
effective weight linearly over a warmup window, so it receives a
growing trickle that lets caches fill and pools warm before it
carries a full load. The cost is honest and small, a slower
return to full capacity after a restart, paid to buy the
stability that a cold backend under full load does not have, and
the module computes the ramp factor so the trickle is a curve an
operator can see rather than an on-off switch that flaps.
"""

from __future__ import annotations

from beacon.errors import Invalid


class SlowStart:
    def __init__(self, window_s: int) -> None:
        if window_s < 0:
            raise Invalid(
                "a negative warmup window is not a duration; the "
                "ramp either takes some time or none"
            )
        self.window_s = window_s

    def ramp_factor(self, age_s: int) -> float:
        if age_s < 0:
            raise Invalid(
                "a backend cannot have a negative age; it went "
                "healthy at some moment, not in the future"
            )
        if self.window_s == 0:
            return 1.0
        return min(1.0, age_s / self.window_s)

    def effective_weight(self, base_weight: float, age_s: int) -> float:
        return base_weight * self.ramp_factor(age_s)

    def is_warming(self, age_s: int) -> bool:
        return self.ramp_factor(age_s) < 1.0
