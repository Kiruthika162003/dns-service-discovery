from __future__ import annotations

import pytest

from beacon.delegationdepth import Descent
from beacon.errors import Invalid, Loop


class TestDescent:
    def test_it_follows_referrals_within_the_budget(self):
        descent = Descent(max_depth=3)
        assert descent.follow_referral() == 1
        assert descent.follow_referral() == 2
        assert descent.follow_referral() == 3

    def test_past_the_budget_it_refuses(self):
        descent = Descent(max_depth=2)
        descent.follow_referral()
        descent.follow_referral()
        with pytest.raises(Loop) as caught:
            descent.follow_referral()
        assert "built to exhaust the resolver" in str(caught.value)

    def test_the_remaining_budget_counts_down(self):
        descent = Descent(max_depth=5)
        descent.follow_referral()
        descent.follow_referral()
        assert descent.remaining() == 3


class TestConstruction:
    def test_a_zero_budget_is_refused(self):
        with pytest.raises(Invalid):
            Descent(max_depth=0)
