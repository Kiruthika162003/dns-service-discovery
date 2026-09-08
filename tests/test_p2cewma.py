from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.p2cewma import P2CEwma


class TestChoice:
    def test_it_picks_the_faster_of_the_two(self):
        balancer = P2CEwma(alpha=0.5)
        balancer.observe("a", 10)
        balancer.observe("b", 100)
        assert balancer.choose("a", "b") == "a"

    def test_it_never_needs_the_global_minimum(self):
        balancer = P2CEwma(alpha=0.5)
        balancer.observe("a", 5)  # global fastest
        balancer.observe("b", 20)
        balancer.observe("c", 30)
        # choosing between b and c never touches a, spreading load
        assert balancer.choose("b", "c") == "b"

    def test_two_identical_candidates_are_refused(self):
        with pytest.raises(Invalid) as caught:
            P2CEwma().choose("a", "a")
        assert "two distinct candidates" in str(caught.value)


class TestAveraging:
    def test_the_average_blends_toward_a_new_sample(self):
        balancer = P2CEwma(alpha=0.5)
        balancer.observe("a", 100)
        assert balancer.observe("a", 200) == 150

    def test_an_unobserved_backend_is_treated_as_fast(self):
        balancer = P2CEwma(alpha=0.5)
        balancer.observe("known", 50)
        # unknown has average 0.0, so it wins
        assert balancer.choose("known", "fresh") == "fresh"
