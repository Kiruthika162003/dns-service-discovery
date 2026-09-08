"""Least connections: send the next request where the fewest are already in flight.

Round robin assumes every request costs the same and every
backend runs at the same speed, and both assumptions fail under
real traffic, where a single slow request pins one backend while
its peers drain their queues. Least connections routes by the one
signal that actually tracks load, the count of requests currently
in flight, sending each new request to the backend with the
fewest outstanding, so a backend stuck on something slow stops
receiving new work until it catches up. It is self-correcting in
a way round robin is not: no backend has to be marked unhealthy
for traffic to steer away from it, because the rising in-flight
count steers automatically and reverses the moment the backend
recovers. The module tracks the outstanding count per backend and
breaks ties deterministically so the routing is testable rather
than a coin flip, and it refuses to route when every backend sits
at its declared connection cap, since past that point least
connections is only choosing which overloaded backend to harm.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class LeastConn:
    def __init__(
        self, backends: list[str], cap: int | None = None
    ) -> None:
        if not backends:
            raise Invalid("no backends to balance across")
        if cap is not None and cap < 1:
            raise Invalid(
                "a connection cap below one admits no request at "
                "all; that is a closed door, not a limit"
            )
        self.cap = cap
        self.inflight = dict.fromkeys(backends, 0)

    def acquire(self) -> str:
        candidates = self.inflight.items()
        if self.cap is not None:
            candidates = [
                (name, count)
                for name, count in candidates
                if count < self.cap
            ]
            if not candidates:
                raise Refused(
                    "every backend is at its connection cap; "
                    "least connections would only pick the "
                    "least-overloaded victim"
                )
        chosen = min(candidates, key=lambda item: (item[1], item[0]))[0]
        self.inflight[chosen] += 1
        return chosen

    def release(self, backend: str) -> None:
        if backend not in self.inflight:
            raise Invalid(
                f"{backend} is not in this balancer; releasing a "
                "connection it never held would drift the counts "
                "negative"
            )
        if self.inflight[backend] == 0:
            raise Invalid(
                f"{backend} has no in-flight request to release; "
                "a double release would undercount its load"
            )
        self.inflight[backend] -= 1

    def load(self) -> dict[str, int]:
        return dict(self.inflight)
