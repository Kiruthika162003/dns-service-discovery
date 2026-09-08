from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.gcra import GCRA


class TestConstruction:
    def test_a_zero_interval_is_refused(self):
        with pytest.raises(Invalid):
            GCRA(emission_interval=0, burst_tolerance=10)

    def test_a_negative_tolerance_is_refused(self):
        with pytest.raises(Invalid):
            GCRA(emission_interval=10, burst_tolerance=-1)


class TestBurst:
    def test_an_initial_burst_within_tolerance_is_allowed(self):
        gcra = GCRA(emission_interval=10, burst_tolerance=20)
        # tolerance 20 over interval 10 allows a burst of 3 at t=0
        assert gcra.allow(0)
        assert gcra.allow(0)
        assert gcra.allow(0)
        assert not gcra.allow(0)

    def test_a_rejected_request_does_not_penalize_later_ones(self):
        gcra = GCRA(emission_interval=10, burst_tolerance=0)
        assert gcra.allow(0)
        assert not gcra.allow(0)  # too soon, rejected
        # rejection did not push the schedule, so the paced one lands
        assert gcra.allow(10)


class TestSteadyRate:
    def test_it_admits_at_the_emission_interval(self):
        gcra = GCRA(emission_interval=10, burst_tolerance=0)
        assert gcra.allow(0)
        assert gcra.allow(10)
        assert gcra.allow(20)

    def test_it_rejects_faster_than_the_interval(self):
        gcra = GCRA(emission_interval=10, burst_tolerance=0)
        assert gcra.allow(0)
        assert not gcra.allow(5)
