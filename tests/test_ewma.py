from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ewma import EwmaBalancer


class TestConstruction:
    def test_an_alpha_outside_the_range_is_refused(self):
        with pytest.raises(Invalid):
            EwmaBalancer(alpha=0)
        with pytest.raises(Invalid):
            EwmaBalancer(alpha=1.5)


class TestAveraging:
    def test_the_first_sample_seeds_the_average(self):
        balancer = EwmaBalancer(alpha=0.3)
        assert balancer.observe("a", 100) == 100

    def test_a_later_sample_blends_toward_it(self):
        balancer = EwmaBalancer(alpha=0.5)
        balancer.observe("a", 100)
        assert balancer.observe("a", 200) == 150

    def test_a_negative_latency_is_refused(self):
        with pytest.raises(Invalid):
            EwmaBalancer().observe("a", -1)


class TestChoosing:
    def test_it_picks_the_lowest_average(self):
        balancer = EwmaBalancer(alpha=0.5)
        balancer.observe("fast", 10)
        balancer.observe("slow", 100)
        assert balancer.choose() == "fast"

    def test_a_slowing_backend_is_avoided_before_it_fails(self):
        balancer = EwmaBalancer(alpha=0.5)
        balancer.observe("a", 10)
        balancer.observe("b", 12)
        # a suddenly slows; its average climbs and b wins
        balancer.observe("a", 200)
        assert balancer.choose() == "b"

    def test_choosing_before_any_observation_is_refused(self):
        with pytest.raises(Invalid):
            EwmaBalancer().choose()
