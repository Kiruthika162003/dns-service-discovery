"""Leaky bucket: a constant drip out, whatever the splash in, so downstream never sees a burst.

A token bucket and a leaky bucket both limit a rate, but they
shape traffic in opposite ways, and choosing wrongly moves a
problem instead of solving it. A token bucket lets a burst
through up to its capacity, which is kind to a bursty client but
passes the burst straight downstream. A leaky bucket does the
reverse: requests pour into a queue of bounded depth and leak out
at a fixed rate no matter how they arrived, so the output is
perfectly smooth and downstream sees a steady drip, at the cost
that the queue adds latency and, once full, overflows and drops.
The leaky bucket is the right tool when the thing being protected
cannot absorb bursts at all, a slow upstream, a rate-limited
third party, and the wrong tool when latency matters more than
smoothness. The module models the level draining at the fixed
rate and the overflow that drops when the queue is full, so the
trade, smooth output bought with queue latency and tail drops, is
visible rather than assumed.
"""

from __future__ import annotations

from beacon.errors import Invalid


class LeakyBucket:
    def __init__(self, leak_rate: float, capacity: float) -> None:
        if leak_rate <= 0:
            raise Invalid(
                "a leak rate of zero never drains; the bucket "
                "fills once and drops everything after, which is a "
                "closed valve, not a limiter"
            )
        if capacity <= 0:
            raise Invalid(
                "a capacity of zero holds no request even for an "
                "instant; there is no queue to smooth with"
            )
        self.leak_rate = leak_rate
        self.capacity = capacity
        self.level = 0.0

    def drain(self, elapsed: float) -> None:
        self.level = max(0.0, self.level - self.leak_rate * elapsed)

    def offer(self, amount: float = 1.0) -> bool:
        if self.level + amount > self.capacity:
            return False
        self.level += amount
        return True

    def overflowing(self) -> bool:
        return self.level >= self.capacity
