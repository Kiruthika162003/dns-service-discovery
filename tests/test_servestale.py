from __future__ import annotations

import pytest

from beacon.errors import Expired, Invalid, Missing
from beacon.servestale import StaleServer


def server() -> StaleServer:
    built = StaleServer()
    built.retire("www.example.com.", "192.0.2.10", expired_at=100)
    return built


class TestTheFences:
    def test_stale_needs_a_real_outage_first(self):
        with pytest.raises(Invalid) as caught:
            server().serve_stale(
                "www.example.com.", now=150, live_failed=False
            )
        assert "not a shortcut around a refresh" in str(
            caught.value
        )

    def test_the_stale_answer_wears_its_age(self):
        verdict = server().serve_stale(
            "www.example.com.", now=150, live_failed=True
        )
        assert "[STALE, expired 50 tick(s) ago]" in verdict
        assert "builds on the dead" in verdict

    def test_past_the_window_stale_becomes_gone(self):
        with pytest.raises(Expired) as caught:
            server().serve_stale(
                "www.example.com.", now=1000, live_failed=True
            )
        assert "graduated from stale to gone" in str(caught.value)

    def test_the_empty_cupboard_is_named(self):
        with pytest.raises(Missing) as caught:
            server().serve_stale(
                "ghost.example.com.", now=150, live_failed=True
            )
        assert "empty cupboard" in str(caught.value)

    def test_a_fresh_answer_does_not_need_this_door(self):
        with pytest.raises(Invalid):
            server().serve_stale(
                "www.example.com.", now=50, live_failed=True
            )


class TestTheLedger:
    def test_the_three_outage_numbers(self):
        built = server()
        built.retire("api.example.com.", "192.0.2.2", expired_at=90)
        built.serve_stale(
            "www.example.com.", now=150, live_failed=True
        )
        built.serve_stale(
            "api.example.com.", now=150, live_failed=True
        )
        with pytest.raises(Expired):
            built.serve_stale(
                "www.example.com.", now=1200, live_failed=True
            )
        ledger = built.outage_ledger()
        assert "2 refusal(s) avoided" in ledger
        assert "110 age-tick(s) served" in ledger
        assert "1 graduation(s) to gone" in ledger
