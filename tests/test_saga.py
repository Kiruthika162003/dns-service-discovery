from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.saga import execute

STEPS = ["register", "dns-record", "certificate"]


class TestExecution:
    def test_a_full_run_commits_with_no_compensation(self):
        outcome, undo = execute(STEPS, fail_at=None)
        assert outcome == "committed"
        assert undo == []

    def test_a_failure_compensates_completed_steps_in_reverse(self):
        outcome, undo = execute(STEPS, fail_at=2)
        assert outcome == "compensated"
        assert undo == ["dns-record", "register"]

    def test_a_failure_at_the_first_step_undoes_nothing(self):
        outcome, undo = execute(STEPS, fail_at=0)
        assert outcome == "compensated"
        assert undo == []


class TestRefusals:
    def test_a_failure_point_past_the_steps_is_refused(self):
        with pytest.raises(Invalid):
            execute(STEPS, fail_at=5)
