"""Welford's online statistics: mean and variance in one pass, without losing precision.

Computing the variance of a stream the obvious way, keeping the sum
and the sum of squares and subtracting, is a numerical trap: for
large values with a small spread, the two large sums nearly cancel
and the subtraction throws away most of the significant digits,
sometimes even yielding a negative variance. Welford's algorithm
sidesteps the cancellation by updating the mean and a running sum of
squared deviations incrementally, one sample at a time. Each new
value shifts the mean by a fraction and contributes to the deviation
accumulator using both the old and new mean, so the accumulator is
always the true sum of squared differences from the current mean, and
the variance is that accumulator over the count, with no giant
intermediate sums to cancel. It is a single pass with a constant
amount of state, so it streams without storing the samples, and it is
stable where the naive formula is not. The cost is a division per
sample rather than a plain addition. The module updates the count,
mean, and deviation accumulator per sample, reports the running mean,
and the sample variance, refusing a variance query before two samples,
since a single point has no spread to measure.
"""

from __future__ import annotations

from beacon.errors import Invalid


class RunningStats:
    def __init__(self) -> None:
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0

    def add(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (value - self.mean)

    def running_mean(self) -> float:
        if self.n == 0:
            raise Invalid("no samples yet; there is no mean of nothing")
        return self.mean

    def sample_variance(self) -> float:
        if self.n < 2:
            raise Invalid(
                "variance needs at least two samples; one point has no "
                "spread to measure"
            )
        return self.m2 / (self.n - 1)
