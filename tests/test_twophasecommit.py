from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.twophasecommit import decide, participant_state


class TestDecision:
    def test_unanimous_yes_commits(self):
        assert decide([True, True, True]) == "commit"

    def test_a_single_no_aborts(self):
        assert decide([True, False, True]) == "abort"

    def test_no_participants_is_refused(self):
        with pytest.raises(Invalid):
            decide([])


class TestParticipantState:
    def test_a_no_voter_aborts(self):
        assert participant_state(voted_yes=False, decision_received=False) == (
            "aborted"
        )

    def test_a_yes_voter_with_the_decision_commits(self):
        assert participant_state(True, decision_received=True) == "committed"

    def test_a_yes_voter_without_the_decision_blocks(self):
        assert participant_state(True, decision_received=False) == (
            "in-doubt-blocked"
        )
