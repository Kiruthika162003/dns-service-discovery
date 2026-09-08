from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.weightedleastrequest import WeightedLeastRequest


class TestConstruction:
    def test_no_backends_is_refused(self):
        with pytest.raises(Invalid):
            WeightedLeastRequest({})

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            WeightedLeastRequest({"a": 0})


class TestCapacityScaling:
    def test_a_bigger_backend_is_kept_more_loaded(self):
        wlr = WeightedLeastRequest({"small": 1.0, "big": 3.0})
        chosen = [wlr.acquire() for _ in range(8)]
        # big should receive roughly three times small's share
        assert chosen.count("big") > chosen.count("small")

    def test_equal_weights_reduce_to_least_request(self):
        wlr = WeightedLeastRequest({"a": 1.0, "b": 1.0})
        assert wlr.acquire() == "a"
        assert wlr.acquire() == "b"
        assert wlr.acquire() == "a"


class TestReleaseAndCost:
    def test_release_lowers_the_load(self):
        wlr = WeightedLeastRequest({"a": 1.0})
        wlr.acquire()
        wlr.release("a")
        assert wlr.load()["a"] == 0

    def test_the_cost_scales_by_weight(self):
        wlr = WeightedLeastRequest({"a": 2.0})
        # (0+1)/2 = 0.5
        assert wlr.cost("a") == 0.5

    def test_a_double_release_is_refused(self):
        wlr = WeightedLeastRequest({"a": 1.0})
        with pytest.raises(Invalid):
            wlr.release("a")
