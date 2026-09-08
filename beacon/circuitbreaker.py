"""A circuit breaker: fail fast when a backend is down, and probe before trusting it again.

Calling a backend that is failing wastes the caller's own
resources on calls that will error, and worse, holds the threads
and connections those calls occupy until they pile into a
cascading failure that spreads upstream. A circuit breaker
watches the failures and, once they cross a threshold, opens: it
stops calling the backend and fails immediately, which gives the
backend room to recover and hands the caller its resources back
at once instead of after a timeout. After a cooldown the breaker
does not slam back to trusting the backend, because a backend
that just failed is guilty until proven healthy; it goes
half-open and lets a single probe through, promoting to closed
only if that probe succeeds and re-opening the instant it fails.
The three states and the transitions between them are the entire
design, and the module makes them explicit so a caller can ask
what the breaker would do at a given moment rather than
discovering it against a live backend the hard way.
"""

from __future__ import annotations

from beacon.errors import Invalid


class CircuitBreaker:
    def __init__(self, threshold: int, cooldown: int) -> None:
        if threshold < 1:
            raise Invalid(
                "a threshold below one would open the breaker "
                "before any failure, wedging it shut from the start"
            )
        self.threshold = threshold
        self.cooldown = cooldown
        self.state = "closed"
        self.failures = 0
        self.opened_at: int | None = None
        self.probe_inflight = False

    def allow(self, now: int) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if now - self.opened_at >= self.cooldown:
                self.state = "half-open"
                self.probe_inflight = True
                return True
            return False
        return not self.probe_inflight

    def on_success(self) -> None:
        if self.state == "half-open":
            self.state = "closed"
            self.probe_inflight = False
        self.failures = 0

    def on_failure(self, now: int) -> None:
        if self.state == "half-open":
            self.state = "open"
            self.opened_at = now
            self.probe_inflight = False
            return
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "open"
            self.opened_at = now
