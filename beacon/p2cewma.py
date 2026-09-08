"""Power of two choices with EWMA: pick the faster of two, sparing the fastest a herd.

Steering every request to the single backend with the lowest
latency average sounds optimal and is a trap: the moment one
backend looks fastest, all traffic piles onto it, its latency
climbs under the load, and by the time the average catches up the
herd has already overwhelmed it, then stampedes to the next
victim. Power of two choices breaks the herd by never consulting
the global minimum. For each request it samples two backends at
random and sends the request to whichever of the two has the lower
latency average, so load spreads across the fleet, no single
backend is everyone's choice at once, and yet each request still
goes to the faster of a real pair rather than blindly. Combined
with an exponentially weighted latency average, the two-choice
comparison catches a backend that is up but slowing, the signal a
health check would miss, without the herding a global minimum
causes. The module tracks the per-backend average, updates it on
each observation, and chooses between exactly two candidates,
breaking ties deterministically so the routing is testable.
"""

from __future__ import annotations

from beacon.errors import Invalid


class P2CEwma:
    def __init__(self, alpha: float = 0.3) -> None:
        if not 0.0 < alpha <= 1.0:
            raise Invalid(
                f"the smoothing factor {alpha} must be in (0, 1]"
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

    def choose(self, first: str, second: str) -> str:
        if first == second:
            raise Invalid(
                "the two choices are the same backend; the power of "
                "two choices needs two distinct candidates to spread "
                "load between"
            )
        a = self.average.get(first, 0.0)
        b = self.average.get(second, 0.0)
        if (a, first) <= (b, second):
            return first
        return second
