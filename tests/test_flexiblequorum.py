from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.flexiblequorum import min_replication_quorum, quorums_intersect


class TestIntersection:
    def test_sizes_summing_over_n_intersect(self):
        # N=5: election 4, replication 2 -> 6 > 5
        assert quorums_intersect(4, 2, n=5)

    def test_sizes_summing_to_n_do_not(self):
        assert not quorums_intersect(3, 2, n=5)

    def test_two_majorities_always_intersect(self):
        assert quorums_intersect(3, 3, n=5)

    def test_a_quorum_larger_than_the_cluster_is_refused(self):
        with pytest.raises(Invalid):
            quorums_intersect(6, 2, n=5)


class TestMinReplication:
    def test_the_smallest_safe_replication_quorum(self):
        # N=5, election 4 -> replication must be >= 2
        assert min_replication_quorum(4, n=5) == 2

    def test_a_small_election_forces_a_large_replication(self):
        # N=5, election 2 -> replication must be >= 4
        assert min_replication_quorum(2, n=5) == 4

    def test_an_oversize_election_quorum_is_refused(self):
        with pytest.raises(Invalid):
            min_replication_quorum(9, n=5)
