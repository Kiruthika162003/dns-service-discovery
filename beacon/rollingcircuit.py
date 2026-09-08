"""A rolling-window circuit breaker: trip on an error rate, not a run of consecutive failures.

A breaker that opens after N consecutive failures is fooled by
interleaving: a backend failing half its requests never strings
together N failures if a success keeps slipping in, so the breaker
stays closed while the backend is plainly broken, serving errors on
every other call. A rolling-window breaker judges by rate instead of
by streak. It counts successes and failures over a recent window and
opens when the failure fraction crosses a threshold, so a backend
that fails half its requests trips regardless of how the failures
and successes are ordered. The window also needs a floor of volume
before it acts, because a single failure out of one request is a
hundred percent failure rate that means nothing, so the breaker
requires a minimum number of samples before a rate can trip it,
which stops it from flapping on tiny samples. The result is a
breaker that reacts to how bad a backend actually is rather than to
the accident of failure ordering. The module tracks the windowed
counts, computes the failure rate, and decides open or closed
against both the rate threshold and the minimum-volume floor.
"""

from __future__ import annotations

from collections import deque

from beacon.errors import Invalid


class RollingCircuit:
    def __init__(
        self, window: int, threshold: float, min_samples: int
    ) -> None:
        if window < 1:
            raise Invalid("a window of zero holds no samples to judge")
        if not 0.0 < threshold <= 1.0:
            raise Invalid(
                f"the failure threshold {threshold} must be in (0, 1]"
            )
        if min_samples < 1:
            raise Invalid(
                "the minimum sample floor must be at least one, or a "
                "single call could trip the breaker"
            )
        self.window = window
        self.threshold = threshold
        self.min_samples = min_samples
        self.samples: deque[bool] = deque(maxlen=window)

    def record(self, success: bool) -> None:
        self.samples.append(success)

    def failure_rate(self) -> float:
        if not self.samples:
            return 0.0
        failures = sum(1 for ok in self.samples if not ok)
        return failures / len(self.samples)

    def is_open(self) -> bool:
        if len(self.samples) < self.min_samples:
            return False
        return self.failure_rate() >= self.threshold
