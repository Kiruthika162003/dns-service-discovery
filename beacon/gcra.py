"""GCRA: a rate limiter that stores one timestamp and needs no refill tick.

The generic cell rate algorithm meters a stream to a rate with a
bounded burst using a single number, a theoretical arrival time,
rather than a bucket of tokens that a background process must
refill on a schedule. It works by imagining the perfectly paced
stream the limiter would allow, one request every emission
interval, and tracking when the next request would be due under
that ideal. A request that arrives at or after its due time is
conforming and pushes the theoretical arrival time forward by one
interval; a request that arrives early is allowed only if it is
within a burst tolerance ahead of the ideal, and otherwise it is
rejected. This is the exact behavior of a token bucket, the two are
mathematical duals, but the state is one timestamp updated on each
request instead of a level decremented by arrivals and incremented
by a timer, so there is no periodic tick to run and no drift
between the tick and real time. The module keeps the theoretical
arrival time, decides conformance against the burst tolerance, and
advances the schedule only for admitted requests, so a rejected
request does not push the ideal forward and penalize the ones that
follow.
"""

from __future__ import annotations

from beacon.errors import Invalid


class GCRA:
    def __init__(
        self, emission_interval: float, burst_tolerance: float
    ) -> None:
        if emission_interval <= 0:
            raise Invalid(
                "the emission interval must be positive; a zero "
                "interval is an unlimited rate, not a limit"
            )
        if burst_tolerance < 0:
            raise Invalid(
                "the burst tolerance is never negative; it is how "
                "far ahead of the ideal a burst may run"
            )
        self.emission_interval = emission_interval
        self.burst_tolerance = burst_tolerance
        self.theoretical_arrival = 0.0

    def allow(self, now: float) -> bool:
        earliest = self.theoretical_arrival - self.burst_tolerance
        if now < earliest:
            return False
        self.theoretical_arrival = (
            max(now, self.theoretical_arrival) + self.emission_interval
        )
        return True
