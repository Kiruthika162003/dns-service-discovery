from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.stridescheduling import StrideScheduler


class TestProportion:
    def test_shares_track_the_weights(self):
        scheduler = StrideScheduler({"a": 3, "b": 1})
        counts = scheduler.run(steps=400)
        # a should get about three times b's turns
        ratio = counts["a"] / counts["b"]
        assert 2.6 < ratio < 3.4

    def test_equal_weights_alternate(self):
        scheduler = StrideScheduler({"a": 1, "b": 1})
        picks = [scheduler.pick() for _ in range(4)]
        assert picks.count("a") == 2
        assert picks.count("b") == 2


class TestDeterminism:
    def test_the_schedule_is_reproducible(self):
        first = StrideScheduler({"a": 3, "b": 1}).run(20)
        second = StrideScheduler({"a": 3, "b": 1}).run(20)
        assert first == second


class TestRefusals:
    def test_no_clients_is_refused(self):
        with pytest.raises(Invalid):
            StrideScheduler({})

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            StrideScheduler({"a": 0})
