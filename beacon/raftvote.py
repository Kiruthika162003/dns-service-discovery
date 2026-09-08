"""Raft's vote: grant only to a candidate at least as current, and at most once per term.

Electing a leader that is missing committed entries would let it
overwrite them, so a Raft node's vote is governed by two rules that
together make that impossible. First, the up-to-date check: a
candidate's log must be at least as current as the voter's, which
means a higher last-log term, or the same term with an index at
least as high, so a candidate whose log trails the voter is refused
and cannot become a leader that would truncate the voter's later
entries. Second, one vote per term: a node votes for at most one
candidate in a given term, so two candidates cannot both collect a
majority and split the cluster into rival leaders. A request from a
stale term is rejected outright, and a request from a newer term
makes the voter step forward to that term and forget any vote it
cast in the old one, which is how the cluster's notion of the
current term ratchets up. The module implements the vote with both
guards and returns the term alongside the decision, since a
rejecting voter still teaches the candidate the newer term it must
catch up to.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Voter:
    current_term: int = 0
    voted_for: str | None = None

    def request_vote(
        self,
        candidate_term: int,
        candidate_id: str,
        candidate_last_index: int,
        candidate_last_term: int,
        my_last_index: int,
        my_last_term: int,
    ) -> tuple[bool, int]:
        if candidate_term < self.current_term:
            return (False, self.current_term)
        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.voted_for = None
        up_to_date = candidate_last_term > my_last_term or (
            candidate_last_term == my_last_term
            and candidate_last_index >= my_last_index
        )
        if self.voted_for in (None, candidate_id) and up_to_date:
            self.voted_for = candidate_id
            return (True, self.current_term)
        return (False, self.current_term)
