from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.nsec3iterations import (
    RECOMMENDED_ITERATIONS,
    defender_pays_more,
    is_harmful,
    per_query_cost,
)


class TestCost:
    def test_more_iterations_cost_more_per_query(self):
        assert per_query_cost(base_cost=1, iterations=0) == 1
        assert per_query_cost(base_cost=1, iterations=10) == 11

    def test_a_negative_iteration_count_is_refused(self):
        with pytest.raises(Invalid):
            per_query_cost(1, -1)


class TestRecommendation:
    def test_zero_is_recommended(self):
        assert RECOMMENDED_ITERATIONS == 0
        assert not is_harmful(0)

    def test_any_positive_count_is_harmful(self):
        assert is_harmful(1)
        assert is_harmful(150)


class TestWhoPays:
    def test_the_message_names_the_asymmetry(self):
        line = defender_pays_more(iterations=10, queries=1000)
        assert "attacker hashes once" in line
        assert "refuted by who pays" in line
