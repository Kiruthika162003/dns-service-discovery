"""A simple moving average: smooth a stream by averaging a fixed window, dropping the oldest.

Smoothing a noisy stream of measurements, a request rate, a latency
reading, to see the trend under the jitter is done two common ways,
and a simple moving average is the one that weights every sample in
its window equally. It keeps the last N values and reports their
mean, so each new sample enters the window and the oldest leaves,
and a running sum makes the update constant time without re-adding
the whole window. The equal weighting is its defining property and
the contrast with an exponentially weighted average, which never
fully forgets an old sample but fades it geometrically. The simple
average forgets abruptly, a sample counts fully until it falls off
the far edge of the window and then not at all, which gives it a
clean hard horizon but also a lag: it responds to a change only as
the window fills with the new regime, trailing the true value by
about half the window. So the window length is the trade, longer
smooths more and lags more, shorter tracks faster and smooths less,
and the choice between a moving average and an exponential one is a
choice between a hard window and a soft decay. The module adds a
sample, evicting the oldest past the window with a running sum, and
reports the current average, refusing an average before any sample.
"""

from __future__ import annotations

from collections import deque

from beacon.errors import Invalid


class MovingAverage:
    def __init__(self, window: int) -> None:
        if window < 1:
            raise Invalid("a moving average needs a window of at least one")
        self.window = window
        self.values: deque[float] = deque()
        self.running_sum = 0.0

    def add(self, value: float) -> None:
        self.values.append(value)
        self.running_sum += value
        if len(self.values) > self.window:
            self.running_sum -= self.values.popleft()

    def average(self) -> float:
        if not self.values:
            raise Invalid("no samples yet; there is no average of nothing")
        return self.running_sum / len(self.values)
