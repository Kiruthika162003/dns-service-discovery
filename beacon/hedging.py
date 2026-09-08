"""Hedged requests: a second try for the slow tail, not a second try for everyone.

Tail latency is the enemy of a service made of many calls,
because a request that fans out to a hundred backends waits for
the slowest, and even a rare slow response becomes common once
you wait for the max of a hundred draws. Hedging attacks the
tail directly: send the request, and if no answer arrives within
a delay set at a high percentile, send a second copy to another
backend and take whichever returns first. The instinct is that
this doubles load, and the instinct is wrong, which is the whole
point. The hedge only fires for the fraction of requests slower
than the delay, so a delay at the ninety-fifth percentile fires
on roughly one request in twenty and adds about five percent
load, not a hundred, while cutting the tail from the slow
backend's latency down to the delay plus a fast backend's. The
module computes the effective latency and the extra load
separately, because the trade only makes sense when both are on
the table: a delay set too low fires too often and the load is
real, a delay set well fires rarely and the tail collapses.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Hedge:
    def __init__(self, hedge_after_ms: int) -> None:
        if hedge_after_ms < 0:
            raise Invalid(
                "a negative hedge delay would fire before the "
                "request was sent; the delay is a wait, not a "
                "head start"
            )
        self.hedge_after_ms = hedge_after_ms

    def fires(self, primary_ms: int) -> bool:
        return primary_ms > self.hedge_after_ms

    def effective_ms(self, primary_ms: int, backup_ms: int) -> int:
        if not self.fires(primary_ms):
            return primary_ms
        return min(primary_ms, self.hedge_after_ms + backup_ms)

    def extra_load_fraction(self, latencies: list[int]) -> float:
        if not latencies:
            raise Invalid(
                "no observed latencies; the hedge rate is a "
                "fraction of requests and there were none"
            )
        fired = sum(1 for value in latencies if self.fires(value))
        return fired / len(latencies)
