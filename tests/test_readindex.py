from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.readindex import read_index_decision


class TestServing:
    def test_a_caught_up_confirmed_leader_serves(self):
        assert (
            read_index_decision(
                commit_index=5,
                applied_index=5,
                leadership_confirmed=True,
            )
            == "serve"
        )

    def test_an_applied_index_ahead_still_serves(self):
        assert (
            read_index_decision(5, 7, leadership_confirmed=True)
            == "serve"
        )


class TestWaiting:
    def test_a_lagging_apply_waits(self):
        assert (
            read_index_decision(5, 3, leadership_confirmed=True)
            == "wait"
        )


class TestLeadership:
    def test_unconfirmed_leadership_is_refused(self):
        with pytest.raises(Refused) as caught:
            read_index_decision(5, 5, leadership_confirmed=False)
        assert "a newer leader has superseded" in str(caught.value)
