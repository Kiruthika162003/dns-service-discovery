"""EWMA load balancing: steer by a decaying latency average, avoiding a slowing backend early.

Routing by health check is coarse and late: a backend has to fail
outright before traffic moves off it, so a backend that is merely
slowing, garbage collecting, swapping, saturating a disk, keeps
getting requests until it crosses the failure line. An exponentially
weighted moving average of each backend's latency gives a finer,
earlier signal. Every observed latency updates the backend's
average by a smoothing factor, so recent slowness pulls the average
up quickly and the balancer steers toward the backend with the
lowest average before any health check would fire. The smoothing
factor is the whole tuning knob and it is a genuine trade: set it
high and the average chases the latest sample, reacting fast but
overreacting to a single unlucky slow response and flapping traffic
around; set it low and the average is stable but sluggish, still
sending requests to a backend that went bad several samples ago.
The module tracks the per-backend average, updates it on each
observation, and picks the lowest, breaking ties deterministically
so the routing is testable rather than a coin flip.
"""

from __future__ import annotations

from beacon.errors import Invalid


class EwmaBalancer:
    def __init__(self, alpha: float = 0.3) -> None:
        if not 0.0 < alpha <= 1.0:
            raise Invalid(
                f"the smoothing factor {alpha} must be in (0, 1]; "
                "zero would never update and above one would "
                "overshoot the sample it averages"
            )
        self.alpha = alpha
        self.average: dict[str, float] = {}

    def observe(self, backend: str, latency: float) -> float:
        if latency < 0:
            raise Invalid("a latency sample is never negative")
        previous = self.average.get(backend)
        if previous is None:
            self.average[backend] = float(latency)
        else:
            self.average[backend] = (
                self.alpha * latency + (1 - self.alpha) * previous
            )
        return self.average[backend]

    def choose(self) -> str:
        if not self.average:
            raise Invalid(
                "no backend has been observed yet; there is no "
                "latency to steer by"
            )
        return min(
            self.average, key=lambda name: (self.average[name], name)
        )
