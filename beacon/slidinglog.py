"""A sliding-window log rate limiter: exact, at the cost of remembering every recent request.

The rate limiters that are cheap are also approximate. A fixed window
admits a double burst at the boundary, and a sliding-window counter
estimates the previous window's contribution rather than knowing it.
The sliding-window log is the exact one, and it pays for exactness in
memory. It keeps the timestamp of every request in the current
window, and to decide a new request it first drops the timestamps
that have aged out of the window and then admits the request only if
fewer than the limit remain, so the count is always the true number
of requests in the trailing window with no estimate and no boundary
artifact. That precision is worth it when a limit must be enforced
exactly, but the cost is honest and can be large: memory grows with
the number of requests in the window, so a high-rate limiter holds a
long log, which is the opposite tradeoff from the counter that holds
two integers and approximates. The module evicts aged timestamps on
each check, admits while the window holds fewer than the limit, and
reports the current window occupancy, so the exactness and its memory
price are both visible.
"""

from __future__ import annotations

from collections import deque

from beacon.errors import Invalid


class SlidingLog:
    def __init__(self, window: int, limit: int) -> None:
        if window <= 0:
            raise Invalid("a window must be a positive duration")
        if limit < 1:
            raise Invalid("a limit below one admits nothing")
        self.window = window
        self.limit = limit
        self.log: deque[int] = deque()

    def _evict(self, now: int) -> None:
        cutoff = now - self.window
        while self.log and self.log[0] <= cutoff:
            self.log.popleft()

    def allow(self, now: int) -> bool:
        self._evict(now)
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False

    def occupancy(self, now: int) -> int:
        self._evict(now)
        return len(self.log)
