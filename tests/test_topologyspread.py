from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.topologyspread import distribute, satisfies, skew


class TestDistribute:
    def test_replicas_spread_evenly(self):
        counts = distribute(6, ["a", "b", "c"])
        assert counts == {"a": 2, "b": 2, "c": 2}

    def test_an_uneven_count_keeps_skew_minimal(self):
        counts = distribute(7, ["a", "b", "c"])
        assert skew(counts) == 1

    def test_existing_placement_is_accounted_for(self):
        counts = distribute(2, ["a", "b", "c"], existing={"a": 2})
        # the two new replicas go to b and c, not a
        assert counts["b"] == 1
        assert counts["c"] == 1
        assert counts["a"] == 2

    def test_existing_in_an_unknown_domain_is_refused(self):
        with pytest.raises(Invalid):
            distribute(1, ["a", "b"], existing={"z": 1})


class TestSatisfies:
    def test_an_even_spread_satisfies_a_skew_of_one(self):
        assert satisfies(distribute(7, ["a", "b", "c"]), max_skew=1)

    def test_a_lopsided_spread_violates(self):
        assert not satisfies({"a": 5, "b": 0}, max_skew=1)

    def test_a_negative_skew_is_refused(self):
        with pytest.raises(Invalid):
            satisfies({"a": 1}, max_skew=-1)
