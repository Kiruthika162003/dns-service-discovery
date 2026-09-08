"""Quota versus rate: two limits that guard different things, and why one is not the other.

A rate limit and a quota are often confused and they protect
against opposite failures. A rate limit caps how fast requests may
arrive, a few per second, and it defends the system from bursts
that would overwhelm it in the moment. A quota caps how much a
client may consume over a long window, ten thousand a day, and it
defends a shared or paid resource from sustained overuse that no
per-second limit would ever catch, because a client can sit
politely under the rate limit every single second and still exhaust
a daily allowance by keeping it up for hours. Enforcing only the
rate leaves the resource open to a slow drain; enforcing only the
quota leaves the system open to a burst that spends the whole
allowance in one spike. So the two are complementary, not
alternatives, and the module implements the quota half: a total
consumed against a limit over a window that resets, refusing a
request that would exceed the remaining allowance and rolling the
window over when its period elapses, so a client is told no when
the day's budget is gone even while it is comfortably within any
rate.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class Quota:
    def __init__(self, limit: int, window: int) -> None:
        if limit <= 0:
            raise Invalid("a quota limit must be positive")
        if window <= 0:
            raise Invalid("a quota window must be a positive duration")
        self.limit = limit
        self.window = window
        self.used = 0
        self.window_start = 0

    def _roll(self, now: int) -> None:
        if now - self.window_start >= self.window:
            self.window_start = now
            self.used = 0

    def consume(self, amount: int, now: int) -> int:
        if amount < 0:
            raise Invalid("a consumption is never negative")
        self._roll(now)
        if self.used + amount > self.limit:
            raise Refused(
                f"the quota of {self.limit} is spent for this "
                f"window; {self.remaining(now)} remains, and a "
                "request within the rate can still exceed the day's "
                "budget"
            )
        self.used += amount
        return self.limit - self.used

    def remaining(self, now: int) -> int:
        self._roll(now)
        return self.limit - self.used
