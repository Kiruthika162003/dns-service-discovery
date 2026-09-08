from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.healthchecks import (
    CheckedInstance,
    HealthBoard,
)


def instance() -> CheckedInstance:
    return CheckedInstance(instance_id="web-1")


class TestGoingDown:
    def test_one_bad_probe_is_weather(self):
        chosen = instance()
        assert chosen.observe(False, now=1) == "web-1 fail (1)"
        assert chosen.healthy

    def test_three_are_climate(self):
        chosen = instance()
        for tick in range(1, 3):
            chosen.observe(False, now=tick)
        verdict = chosen.observe(False, now=3)
        assert "3 are climate" in verdict
        assert not chosen.healthy

    def test_a_pass_resets_the_weather(self):
        chosen = instance()
        chosen.observe(False, now=1)
        chosen.observe(False, now=2)
        chosen.observe(True, now=3)
        chosen.observe(False, now=4)
        assert chosen.healthy


class TestComingBack:
    def sick(self) -> CheckedInstance:
        chosen = instance()
        for tick in range(1, 4):
            chosen.observe(False, now=tick)
        return chosen

    def test_recovery_takes_the_longer_streak(self):
        chosen = self.sick()
        for tick in range(4, 8):
            chosen.observe(True, now=tick)
        assert not chosen.healthy
        verdict = chosen.observe(True, now=8)
        assert "flapping back early kills real requests" in (
            verdict
        )
        assert chosen.healthy

    def test_a_fail_mid_recovery_restarts_the_earning(self):
        chosen = self.sick()
        for tick in range(4, 8):
            chosen.observe(True, now=tick)
        chosen.observe(False, now=8)
        for tick in range(9, 13):
            chosen.observe(True, now=tick)
        assert not chosen.healthy


class TestTheBoard:
    def test_double_tracking_is_refused(self):
        board = HealthBoard()
        board.track("web-1")
        with pytest.raises(Invalid):
            board.track("web-1")

    def test_the_coin_is_named_and_pulled(self):
        board = HealthBoard()
        board.track("web-1")
        tick = 0
        for _ in range(4):
            for _ in range(3):
                tick += 1
                board.observe("web-1", False, now=tick)
            for _ in range(5):
                tick += 1
                board.observe("web-1", True, now=tick)
        report = board.flap_report()
        assert "1 instance(s) flipping like coins" in report
        assert (
            "web-1: 8 transition(s); pulled for diagnosis"
        ) in report

    def test_an_earned_state_is_not_a_coin(self):
        board = HealthBoard()
        board.track("web-1")
        for tick in range(1, 4):
            board.observe("web-1", False, now=tick)
        assert board.flap_report() == (
            "no coins on the board; states are earned"
        )
