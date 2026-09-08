from __future__ import annotations

import pytest

from beacon.aggressivensec import can_answer_from_cache, covers
from beacon.errors import Invalid


class TestCovers:
    def test_a_name_inside_the_gap_is_covered(self):
        # between "alpha" and "gamma", "beta" does not exist
        assert covers("alpha.example.", "gamma.example.", "beta.example.")

    def test_a_name_outside_the_gap_is_not(self):
        assert not covers("alpha.example.", "gamma.example.", "zeta.example.")

    def test_the_wraparound_gap_at_the_apex(self):
        # last name "zeta" wraps to the apex "example."; "zzz" sorts after zeta
        assert covers("zeta.example.", "example.", "zzz.example.")


class TestCache:
    def test_a_covering_gap_answers_from_cache(self):
        gaps = [("alpha.example.", "gamma.example.")]
        assert can_answer_from_cache("beta.example.", gaps)

    def test_an_uncovered_name_needs_upstream(self):
        gaps = [("alpha.example.", "gamma.example.")]
        assert not can_answer_from_cache("zeta.example.", gaps)

    def test_no_cached_nsec_is_refused(self):
        with pytest.raises(Invalid) as caught:
            can_answer_from_cache("beta.example.", [])
        assert "must go upstream" in str(caught.value)
