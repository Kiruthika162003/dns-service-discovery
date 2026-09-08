from __future__ import annotations

import pytest

from beacon.commitindex import commit_index
from beacon.errors import Invalid


class TestMajority:
    def test_an_entry_on_a_majority_commits(self):
        # leader 5, two followers at 5, two behind -> 3 of 5 have 5
        match = [5, 5, 5, 3, 2]
        terms = {5: 3, 3: 3, 2: 1}
        assert commit_index(match, current_term=3, entry_terms=terms) == 5

    def test_an_entry_short_of_a_majority_does_not_commit(self):
        # only 2 of 5 have index 5
        match = [5, 5, 3, 3, 2]
        terms = {5: 3, 3: 3, 2: 1}
        assert commit_index(match, current_term=3, entry_terms=terms) == 3


class TestTheTermRule:
    def test_an_old_term_entry_is_not_committed_on_its_own(self):
        # index 5 is on a majority but from term 2, not the current 3
        match = [5, 5, 5, 4, 4]
        terms = {5: 2, 4: 2}
        # nothing in the current term is on a majority -> commit 0
        assert commit_index(match, current_term=3, entry_terms=terms) == 0

    def test_a_current_term_entry_carries_earlier_ones_forward(self):
        # index 6 current-term on a majority commits, above old 5
        match = [6, 6, 6, 5, 5]
        terms = {6: 3, 5: 2}
        assert commit_index(match, current_term=3, entry_terms=terms) == 6


class TestRefusals:
    def test_an_empty_match_list_is_refused(self):
        with pytest.raises(Invalid):
            commit_index([], current_term=1, entry_terms={})
