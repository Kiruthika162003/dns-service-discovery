"""An adaptive concurrency limit: read the queue's edge from latency, not from a guess.

A fixed concurrency limit is a guess that is wrong in both
directions. Too low and the backend idles under a cap it could
easily exceed; too high and requests pile into a queue that adds
only latency, never throughput, because a saturated server does
not go faster for being asked harder. Little's law points the way
out: the useful in-flight count is throughput times the minimum
latency, so the limit can be discovered from latency rather than
guessed. When the current latency sits near the observed minimum
the queue is empty and the limit may grow; when latency climbs
above the minimum a queue is forming and the limit must shrink,
and the gradient, the ratio of minimum latency to current
latency, sets how sharply. The module implements that gradient
step with a headroom allowance so a healthy system can probe
upward, and holds one invariant without exception: the limit
never drops below one, because a limit of zero would wedge the
system shut with no request able to test whether it has recovered.
"""

from __future__ import annotations

from math import sqrt

from beacon.errors import Invalid


class GradientLimiter:
    def __init__(self, limit: float, min_rtt: float) -> None:
        if limit < 1:
            raise Invalid(
                "a starting limit below one admits no request to "
                "measure with; start at one or more"
            )
        if min_rtt <= 0:
            raise Invalid(
                "the minimum latency must be positive; a "
                "zero minimum would divide the gradient by nothing"
            )
        self.limit = float(limit)
        self.min_rtt = float(min_rtt)

    def observe(self, sample_rtt: float) -> float:
        if sample_rtt <= 0:
            raise Invalid(
                "a non-positive latency sample is impossible; a "
                "request took some time to answer"
            )
        self.min_rtt = min(self.min_rtt, sample_rtt)
        gradient = max(0.5, min(1.0, self.min_rtt / sample_rtt))
        headroom = sqrt(self.limit)
        self.limit = max(1.0, self.limit * gradient + headroom)
        return self.limit

    def queueing(self, sample_rtt: float) -> bool:
        return sample_rtt > self.min_rtt
