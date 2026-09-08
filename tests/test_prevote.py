from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.prevote import can_start_election, would_grant_prevote


class TestGrant:
    def test_a_peer_with_a_leader_refuses_the_prevote(self):
        assert not would_grant_prevote(
            peer_has_leader=True,
            candidate_last_index=9,
            candidate_last_term=5,
            peer_last_index=1,
            peer_last_term=1,
        )

    def test_a_leaderless_peer_grants_to_a_current_log(self):
        assert would_grant_prevote(
            peer_has_leader=False,
            candidate_last_index=9,
            candidate_last_term=5,
            peer_last_index=9,
            peer_last_term=5,
        )

    def test_a_behind_candidate_is_refused_even_without_a_leader(
        self,
    ):
        assert not would_grant_prevote(
            peer_has_leader=False,
            candidate_last_index=2,
            candidate_last_term=1,
            peer_last_index=9,
            peer_last_term=5,
        )


class TestElection:
    def test_a_majority_of_prevotes_permits_an_election(self):
        assert can_start_election(prevotes_granted=3, cluster_size=5)

    def test_short_of_a_majority_stands_down(self):
        assert not can_start_election(prevotes_granted=2, cluster_size=5)

    def test_an_empty_cluster_is_refused(self):
        with pytest.raises(Invalid):
            can_start_election(0, 0)
