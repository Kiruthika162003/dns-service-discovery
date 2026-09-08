from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.serialmath import (
    MODULUS,
    bump,
    newer,
    recovery_plan,
)


class TestNewer:
    def test_plain_ordering_works_on_the_near_side(self):
        assert newer(2026090902, 2026090901)
        assert not newer(2026090901, 2026090902)

    def test_the_wrap_is_still_forward(self):
        assert newer(5, MODULUS - 5)

    def test_equal_serials_are_not_newer(self):
        assert not newer(7, 7)

    def test_the_half_circle_pair_is_incomparable_by_design(self):
        with pytest.raises(Invalid) as caught:
            newer(2**31, 0)
        assert "forward is a coin flip" in str(caught.value)

    def test_serials_live_on_the_circle_or_not_at_all(self):
        with pytest.raises(Invalid):
            newer(MODULUS, 0)


class TestBumping:
    def test_the_bump_wraps_the_circle(self):
        assert bump(MODULUS - 1) == 0

    def test_a_half_circle_bump_breaks_newer(self):
        with pytest.raises(Invalid) as caught:
            bump(0, by=2**31)
        assert "newer stops meaning anything" in str(caught.value)


class TestTheRecovery:
    def test_the_easy_case_is_one_publish(self):
        assert recovery_plan(100, 200) == [200]

    def test_the_fat_finger_walks_the_long_way_around(self):
        plan = recovery_plan(4000000000, 2026090901)
        assert len(plan) == 2
        assert plan[-1] == 2026090901
        position = 4000000000
        for step in plan:
            assert newer(step, position)
            position = step

    def test_already_there_needs_no_plan(self):
        with pytest.raises(Invalid):
            recovery_plan(5, 5)
