from __future__ import annotations

from beacon.raftvote import Voter


class TestGranting:
    def test_a_current_candidate_wins_the_vote(self):
        voter = Voter(current_term=1)
        granted, term = voter.request_vote(
            candidate_term=2,
            candidate_id="c1",
            candidate_last_index=5,
            candidate_last_term=1,
            my_last_index=5,
            my_last_term=1,
        )
        assert granted
        assert term == 2

    def test_a_newer_term_resets_the_vote(self):
        voter = Voter(current_term=1, voted_for="old")
        granted, _ = voter.request_vote(3, "c2", 9, 2, 5, 1)
        assert granted
        assert voter.voted_for == "c2"


class TestTheUpToDateCheck:
    def test_a_behind_candidate_is_refused(self):
        voter = Voter(current_term=1)
        granted, _ = voter.request_vote(
            candidate_term=2,
            candidate_id="c1",
            candidate_last_index=3,
            candidate_last_term=1,
            my_last_index=7,
            my_last_term=1,
        )
        assert not granted

    def test_a_higher_last_term_beats_a_higher_index(self):
        voter = Voter(current_term=1)
        granted, _ = voter.request_vote(2, "c1", 1, 5, 100, 4)
        assert granted


class TestOneVotePerTerm:
    def test_a_second_candidate_in_the_term_is_refused(self):
        voter = Voter(current_term=1)
        voter.request_vote(2, "c1", 5, 1, 5, 1)
        granted, _ = voter.request_vote(2, "c2", 5, 1, 5, 1)
        assert not granted

    def test_a_stale_term_candidate_is_refused(self):
        voter = Voter(current_term=5)
        granted, term = voter.request_vote(3, "c1", 9, 4, 1, 1)
        assert not granted
        assert term == 5
