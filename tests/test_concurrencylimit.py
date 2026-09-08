from __future__ import annotations

import pytest

from beacon.concurrencylimit import GradientLimiter
from beacon.errors import Invalid


class TestConstruction:
    def test_a_limit_below_one_is_refused(self):
        with pytest.raises(Invalid):
            GradientLimiter(limit=0, min_rtt=10)

    def test_a_nonpositive_min_rtt_is_refused(self):
        with pytest.raises(Invalid):
            GradientLimiter(limit=10, min_rtt=0)


class TestGradient:
    def test_latency_at_the_minimum_grows_the_limit(self):
        limiter = GradientLimiter(limit=10, min_rtt=10)
        assert limiter.observe(10) > 10

    def test_latency_above_the_minimum_shrinks_the_limit(self):
        limiter = GradientLimiter(limit=10, min_rtt=10)
        assert limiter.observe(1000) < 10

    def test_the_limit_never_falls_below_one(self):
        limiter = GradientLimiter(limit=1, min_rtt=10)
        for _ in range(20):
            limiter.observe(100000)
        assert limiter.limit >= 1.0

    def test_a_faster_sample_lowers_the_observed_minimum(self):
        limiter = GradientLimiter(limit=10, min_rtt=10)
        limiter.observe(5)
        assert limiter.min_rtt == 5

    def test_a_nonpositive_sample_is_refused(self):
        with pytest.raises(Invalid):
            GradientLimiter(10, 10).observe(0)


class TestQueueing:
    def test_queueing_is_detected_above_the_minimum(self):
        limiter = GradientLimiter(limit=10, min_rtt=10)
        assert limiter.queueing(20)
        assert not limiter.queueing(10)
