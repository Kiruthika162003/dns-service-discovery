from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lotteryscheduling import expected_share, winner

ALLOC = {"a": 3, "b": 1}  # sorted: a holds tickets 0,1,2 ; b holds 3


class TestWinner:
    def test_a_draw_in_the_first_range_picks_that_holder(self):
        assert winner(ALLOC, draw=0) == "a"
        assert winner(ALLOC, draw=2) == "a"

    def test_a_draw_in_the_next_range_picks_the_next(self):
        assert winner(ALLOC, draw=3) == "b"

    def test_a_draw_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            winner(ALLOC, draw=4)

    def test_no_tickets_is_refused(self):
        with pytest.raises(Invalid):
            winner({}, draw=0)


class TestShare:
    def test_expected_share_is_tickets_over_total(self):
        assert expected_share(ALLOC, "a") == 0.75
        assert expected_share(ALLOC, "b") == 0.25

    def test_a_client_with_no_tickets_has_no_share(self):
        assert expected_share(ALLOC, "c") == 0.0
