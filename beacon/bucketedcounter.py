"""A bucketed sliding-window counter: a light rate estimate that lags a spike by one bucket.

Measuring a rate over a sliding window can be done exactly by keeping
every event's timestamp, but that costs memory proportional to the
traffic. A bucketed counter trades that exactness for a fixed, tiny
footprint. It divides the window into a set of time buckets, each
holding a count, and a record simply increments the bucket for the
current instant, while a rate query sums the buckets that still fall
within the trailing window, dropping those that have aged out. The
memory is the number of buckets, constant regardless of how many
events arrive, which is the win over the per-event log. The cost is
resolution: the counter cannot see timing finer than a bucket, so it
lags a sudden spike by up to one bucket and cannot distinguish events
that share a bucket, a coarser view than the exact log gives for far
less memory. Choosing the bucket width sets the trade between
resolution and footprint. The module records into the current bucket,
sums the buckets within the window for the rate, evicts buckets that
have fallen out of the window, and refuses a non-positive bucket
width or window, which describe no window at all.
"""

from __future__ import annotations

from beacon.errors import Invalid


class BucketedCounter:
    def __init__(self, window: int, bucket_width: int) -> None:
        if window <= 0 or bucket_width <= 0:
            raise Invalid("the window and bucket width must be positive")
        if bucket_width > window:
            raise Invalid(
                "a bucket wider than the window holds more than the "
                "window measures; the bucket must divide the window"
            )
        self.window = window
        self.bucket_width = bucket_width
        self.buckets: dict[int, int] = {}

    def _bucket(self, now: int) -> int:
        return now // self.bucket_width

    def _evict(self, now: int) -> None:
        oldest = self._bucket(now - self.window + 1)
        for bucket in list(self.buckets):
            if bucket < oldest:
                del self.buckets[bucket]

    def record(self, now: int) -> None:
        self._evict(now)
        self.buckets[self._bucket(now)] = self.buckets.get(self._bucket(now), 0) + 1

    def count(self, now: int) -> int:
        self._evict(now)
        return sum(self.buckets.values())
