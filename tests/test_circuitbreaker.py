from __future__ import annotations

import pytest

from beacon.circuitbreaker import CircuitBreaker
from beacon.errors import Invalid


class TestConstruction:
    def test_a_threshold_below_one_is_refused(self):
        with pytest.raises(Invalid):
            CircuitBreaker(threshold=0, cooldown=10)


class TestOpening:
    def test_the_breaker_stays_closed_below_the_threshold(self):
        breaker = CircuitBreaker(threshold=3, cooldown=10)
        breaker.on_failure(now=1)
        breaker.on_failure(now=2)
        assert breaker.allow(now=3)

    def test_crossing_the_threshold_opens_it(self):
        breaker = CircuitBreaker(threshold=3, cooldown=10)
        for tick in range(3):
            breaker.on_failure(now=tick)
        assert not breaker.allow(now=5)

    def test_a_success_resets_the_failure_count(self):
        breaker = CircuitBreaker(threshold=3, cooldown=10)
        breaker.on_failure(now=1)
        breaker.on_failure(now=2)
        breaker.on_success()
        breaker.on_failure(now=3)
        assert breaker.allow(now=4)


class TestHalfOpenProbe:
    def open_breaker(self) -> CircuitBreaker:
        breaker = CircuitBreaker(threshold=1, cooldown=10)
        breaker.on_failure(now=0)
        return breaker

    def test_after_cooldown_one_probe_is_allowed(self):
        breaker = self.open_breaker()
        assert not breaker.allow(now=5)
        assert breaker.allow(now=10)
        assert breaker.state == "half-open"

    def test_a_second_probe_is_blocked_while_the_first_runs(self):
        breaker = self.open_breaker()
        assert breaker.allow(now=10)
        assert not breaker.allow(now=11)

    def test_a_successful_probe_closes_the_breaker(self):
        breaker = self.open_breaker()
        breaker.allow(now=10)
        breaker.on_success()
        assert breaker.state == "closed"
        assert breaker.allow(now=12)

    def test_a_failed_probe_reopens_immediately(self):
        breaker = self.open_breaker()
        breaker.allow(now=10)
        breaker.on_failure(now=11)
        assert breaker.state == "open"
        assert not breaker.allow(now=12)
