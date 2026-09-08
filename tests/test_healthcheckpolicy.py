from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.healthcheckpolicy import HealthCheck


class TestConstruction:
    def test_a_zero_threshold_is_refused(self):
        with pytest.raises(Invalid):
            HealthCheck(rise=0, fall=3)


class TestFall:
    def test_it_takes_the_fall_threshold_to_eject(self):
        hc = HealthCheck(rise=2, fall=3, healthy=True)
        hc.record(False)
        hc.record(False)
        assert hc.in_pool()  # two failures, threshold three
        hc.record(False)
        assert not hc.in_pool()

    def test_a_success_resets_the_failure_streak(self):
        hc = HealthCheck(rise=2, fall=3, healthy=True)
        hc.record(False)
        hc.record(False)
        hc.record(True)  # streak broken
        hc.record(False)
        hc.record(False)
        assert hc.in_pool()  # only two consecutive again


class TestRise:
    def test_it_takes_the_rise_threshold_to_readmit(self):
        hc = HealthCheck(rise=3, fall=1, healthy=False)
        hc.record(True)
        hc.record(True)
        assert not hc.in_pool()  # two successes, threshold three
        hc.record(True)
        assert hc.in_pool()

    def test_a_failure_resets_the_success_streak(self):
        hc = HealthCheck(rise=3, fall=1, healthy=False)
        hc.record(True)
        hc.record(True)
        hc.record(False)  # streak broken
        hc.record(True)
        hc.record(True)
        assert not hc.in_pool()  # only two consecutive again
