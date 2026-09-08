from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.maintenance import MaintenanceBoard


def board() -> MaintenanceBoard:
    built = MaintenanceBoard()
    built.enter("web-1", now=0, duration=30, reason="deploy 3.2")
    return built


class TestEntering:
    def test_maintenance_suppresses_the_page(self):
        verdict = MaintenanceBoard().enter(
            "web-9", now=0, duration=30, reason="patch"
        )
        assert "failed checks expected, not paged" in verdict

    def test_a_reasonless_window_is_an_undeclared_outage(self):
        with pytest.raises(Invalid) as caught:
            MaintenanceBoard().enter(
                "web-1", now=0, duration=10, reason="  "
            )
        assert "an outage someone forgot to declare" in str(
            caught.value
        )

    def test_a_zero_duration_is_a_flicker(self):
        with pytest.raises(Invalid):
            MaintenanceBoard().enter(
                "web-1", now=0, duration=0, reason="x"
            )

    def test_double_entry_is_refused(self):
        with pytest.raises(Invalid):
            board().enter("web-1", now=5, duration=10, reason="y")


class TestExpectedDown:
    def test_a_down_check_inside_the_window_is_expected(self):
        assert board().is_expected_down("web-1", now=15)

    def test_a_down_check_past_the_window_is_not(self):
        assert not board().is_expected_down("web-1", now=31)

    def test_leaving_returns_to_rotation(self):
        chosen = board()
        assert chosen.leave("web-1") == "web-1 back in rotation"
        with pytest.raises(Missing):
            chosen.leave("web-1")


class TestTheBoard:
    def test_planned_and_overrun_are_kept_apart(self):
        chosen = board()
        chosen.enter("web-2", now=20, duration=100, reason="soak")
        report = chosen.board_report(now=40)
        assert "1 planned absence(s), 1 overrun(s)" in report
        assert (
            "web-1: overrun by 10 tick(s) (deploy 3.2)"
        ) in report
        assert "the deploy that hung and nobody noticed" in report

    def test_a_clean_board_escalates_nothing(self):
        report = board().board_report(now=10)
        assert "1 planned absence(s), 0 overrun(s)" in report
        assert "escalate" not in report
