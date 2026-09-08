from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rollingcircuit import RollingCircuit


class TestConstruction:
    def test_a_bad_threshold_is_refused(self):
        with pytest.raises(Invalid):
            RollingCircuit(window=10, threshold=1.5, min_samples=5)

    def test_a_zero_min_samples_is_refused(self):
        with pytest.raises(Invalid):
            RollingCircuit(window=10, threshold=0.5, min_samples=0)


class TestInterleavedFailures:
    def test_alternating_failures_still_trip_the_breaker(self):
        breaker = RollingCircuit(window=10, threshold=0.5, min_samples=4)
        for i in range(10):
            breaker.record(success=(i % 2 == 0))  # 50% failures, alternating
        assert breaker.failure_rate() == 0.5
        assert breaker.is_open()

    def test_a_healthy_backend_stays_closed(self):
        breaker = RollingCircuit(window=10, threshold=0.5, min_samples=4)
        for _ in range(10):
            breaker.record(success=True)
        assert not breaker.is_open()


class TestMinSamples:
    def test_a_single_failure_does_not_trip_below_the_floor(self):
        breaker = RollingCircuit(window=10, threshold=0.5, min_samples=5)
        breaker.record(success=False)
        assert breaker.failure_rate() == 1.0
        assert not breaker.is_open()  # only one sample, below the floor

    def test_the_window_forgets_old_samples(self):
        breaker = RollingCircuit(window=4, threshold=0.5, min_samples=4)
        for _ in range(4):
            breaker.record(success=False)
        assert breaker.is_open()
        for _ in range(4):
            breaker.record(success=True)  # push the failures out
        assert not breaker.is_open()
