from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.gossipconvergence import coverage_after, rounds_to_converge


class TestCoverage:
    def test_it_starts_at_one_infected(self):
        assert coverage_after(nodes=1000, fanout=2, rounds=0) == 1

    def test_it_grows_multiplicatively(self):
        # 1 -> 3 -> 9 with fanout 2
        assert coverage_after(1000, fanout=2, rounds=1) == 3
        assert coverage_after(1000, fanout=2, rounds=2) == 9

    def test_it_caps_at_the_cluster_size(self):
        assert coverage_after(10, fanout=2, rounds=100) == 10

    def test_a_zero_fanout_is_refused(self):
        with pytest.raises(Invalid):
            coverage_after(10, fanout=0, rounds=1)


class TestConvergence:
    def test_convergence_is_logarithmic_in_size(self):
        small = rounds_to_converge(1000, fanout=2)
        big = rounds_to_converge(1000000, fanout=2)
        # 1000x the nodes, only a handful more rounds
        assert big < small + 12

    def test_a_bigger_fanout_converges_faster(self):
        slow = rounds_to_converge(10000, fanout=2)
        fast = rounds_to_converge(10000, fanout=8)
        assert fast < slow
