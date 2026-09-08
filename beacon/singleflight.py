"""Single-flight: collapse a burst of identical lookups into one, turning a herd into a query.

When a popular name's cache entry expires, every request that
arrives before the refill completes piles into the same upstream
lookup, a cache stampede that hits the authority with a thousand
identical queries for an answer that one query would have
supplied to all of them. Single-flight coalesces the herd. The
first request for a key becomes the in-flight leader and actually
goes upstream, and every later request for the same key while that
fetch is outstanding attaches to it as a waiter instead of
launching its own, so when the leader returns all the waiters are
served from the single result. The saving is exactly the stampede:
a thousand concurrent requests become one upstream query and nine
hundred ninety-nine waiters riding on it. The one rule that keeps
it correct is that a flight ends when its result lands, so a
request arriving after that starts a fresh flight rather than
attaching to a completed one and waiting forever, and the module
models the in-flight registry with that lifecycle explicit:
leading, joining, and completing.
"""

from __future__ import annotations

from beacon.errors import Invalid


class SingleFlight:
    def __init__(self) -> None:
        self.inflight: dict[str, int] = {}

    def begin(self, key: str) -> str:
        if key in self.inflight:
            self.inflight[key] += 1
            return "joined"
        self.inflight[key] = 1
        return "leader"

    def waiters(self, key: str) -> int:
        return self.inflight.get(key, 0)

    def complete(self, key: str) -> int:
        if key not in self.inflight:
            raise Invalid(
                f"no flight for {key} to complete; a result cannot "
                "land for a flight that never began"
            )
        return self.inflight.pop(key)

    def upstream_saved(self, concurrent: int, key: str) -> int:
        served = self.inflight.get(key, 0)
        if concurrent < served:
            raise Invalid(
                "more requests are recorded in flight than were "
                "counted concurrent; the accounting is inconsistent"
            )
        return served - 1 if served else 0
