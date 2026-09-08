"""Phi accrual failure detection: a rising suspicion instead of a single yes-or-no timeout.

A hard timeout answers is it dead with a boolean and forces one
threshold to serve every situation, so it is either too twitchy
for a jittery network or too slow for a responsive one. The phi
accrual detector replaces the boolean with a continuous number.
It models the intervals between heartbeats and, given how long it
has been since the last one, reports phi, the negative log of the
probability that a heartbeat this late is still normal, so phi
climbs smoothly as silence stretches and different callers can set
different thresholds against the same signal, a cautious one
waiting for phi of twelve and an eager one acting at eight. The
value of the accrual approach is that the suspicion is graded and
adapts to the observed rhythm: a link that normally beats every
second and a link that beats every ten produce the same phi at the
same relative lateness, so the threshold means the same thing on
both. The module computes phi under an exponential model and
refuses a nonpositive mean interval, since a rhythm of zero has no
lateness to measure against.
"""

from __future__ import annotations

import math

from beacon.errors import Invalid


class PhiDetector:
    def __init__(self, mean_interval: float) -> None:
        if mean_interval <= 0:
            raise Invalid(
                "the mean heartbeat interval must be positive; a "
                "rhythm of zero has no lateness to measure against"
            )
        self.mean_interval = mean_interval

    def phi(self, elapsed: float) -> float:
        if elapsed < 0:
            raise Invalid(
                "elapsed time since the last heartbeat cannot be "
                "negative; a beat does not arrive from the future"
            )
        probability = math.exp(-elapsed / self.mean_interval)
        if probability <= 0:
            return math.inf
        return -math.log10(probability)

    def suspect(self, elapsed: float, threshold: float = 8.0) -> bool:
        return self.phi(elapsed) >= threshold
