from __future__ import annotations

import pytest

from beacon.adaptivesampling import AdaptiveSampler
from beacon.errors import Invalid


def sampler() -> AdaptiveSampler:
    return AdaptiveSampler(slow_threshold_ms=500, base_rate=0.01)


class TestKeep:
    def test_every_error_is_kept(self):
        assert sampler().keep(is_error=True, latency_ms=10, draw=0.99)

    def test_every_slow_request_is_kept(self):
        assert sampler().keep(is_error=False, latency_ms=800, draw=0.99)

    def test_a_boring_request_is_usually_dropped(self):
        assert not sampler().keep(is_error=False, latency_ms=10, draw=0.5)

    def test_a_boring_request_under_the_rate_is_kept(self):
        assert sampler().keep(is_error=False, latency_ms=10, draw=0.005)


class TestInteresting:
    def test_errors_and_slow_are_interesting(self):
        assert sampler().is_interesting(True, 10)
        assert sampler().is_interesting(False, 600)

    def test_a_fast_success_is_not(self):
        assert not sampler().is_interesting(False, 50)


class TestKeepRate:
    def test_the_rate_reflects_the_mix(self):
        traces = [
            (True, 10, 0.9),  # error, kept
            (False, 700, 0.9),  # slow, kept
            (False, 10, 0.9),  # boring, dropped
            (False, 10, 0.9),  # boring, dropped
        ]
        assert sampler().keep_rate(traces) == 0.5

    def test_no_traces_is_refused(self):
        with pytest.raises(Invalid):
            sampler().keep_rate([])
