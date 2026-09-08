from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.weightedreservoir import WeightedReservoir


class TestFilling:
    def test_it_fills_to_capacity(self):
        res = WeightedReservoir(capacity=2)
        res.offer("a", weight=1.0, draw=0.5)
        res.offer("b", weight=1.0, draw=0.5)
        assert set(res.contents()) == {"a", "b"}


class TestWeighting:
    def test_a_heavy_item_with_a_good_draw_displaces_a_light_one(self):
        res = WeightedReservoir(capacity=1)
        # light item, small key
        res.offer("light", weight=1.0, draw=0.1)
        # heavy item, big key: 0.5 ** (1/10) is close to 1
        res.offer("heavy", weight=10.0, draw=0.5)
        assert res.contents() == ["heavy"]

    def test_a_weak_draw_does_not_always_displace(self):
        res = WeightedReservoir(capacity=1)
        res.offer("resident", weight=1.0, draw=0.99)
        # a much smaller key does not replace the strong resident
        res.offer("challenger", weight=1.0, draw=0.01)
        assert res.contents() == ["resident"]


class TestRefusals:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            WeightedReservoir(0)

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            WeightedReservoir(2).offer("a", weight=0, draw=0.5)

    def test_a_zero_draw_is_refused(self):
        with pytest.raises(Invalid):
            WeightedReservoir(2).offer("a", weight=1, draw=0.0)
