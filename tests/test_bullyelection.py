from __future__ import annotations

import pytest

from beacon.bullyelection import (
    disrupts_on_recovery,
    election_outcome,
    leader,
)
from beacon.errors import Invalid


class TestOutcome:
    def test_no_higher_node_wins(self):
        assert election_outcome(5, alive_higher=[]) == "win"

    def test_a_higher_node_defers(self):
        assert election_outcome(5, alive_higher=[7, 9]) == "defer"

    def test_a_non_higher_id_in_the_set_is_refused(self):
        with pytest.raises(Invalid):
            election_outcome(5, alive_higher=[3])


class TestLeader:
    def test_the_highest_id_leads(self):
        assert leader([2, 7, 4]) == 7

    def test_an_empty_set_is_refused(self):
        with pytest.raises(Invalid):
            leader([])


class TestDisruption:
    def test_a_higher_recovering_node_disrupts(self):
        assert disrupts_on_recovery(recovering_id=9, current_leader_id=7)

    def test_a_lower_recovering_node_does_not(self):
        assert not disrupts_on_recovery(3, current_leader_id=7)
