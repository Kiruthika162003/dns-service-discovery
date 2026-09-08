from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.floydwarshall import all_pairs


class TestAllPairs:
    def test_a_two_hop_path_beats_the_direct_edge(self):
        edges = [(0, 1, 3), (1, 2, 4), (0, 2, 10)]
        distance = all_pairs(3, edges)
        assert distance[0][2] == 7

    def test_each_vertex_reaches_itself_at_zero(self):
        distance = all_pairs(3, [(0, 1, 5)])
        assert all(distance[i][i] == 0 for i in range(3))

    def test_an_unreachable_pair_stays_at_infinity(self):
        distance = all_pairs(2, [])
        assert distance[0][1] == float("inf")

    def test_negative_edges_are_handled(self):
        edges = [(0, 1, 4), (1, 2, -2), (0, 2, 5)]
        assert all_pairs(3, edges)[0][2] == 2


class TestNegativeCycle:
    def test_a_negative_cycle_is_reported(self):
        edges = [(0, 1, 1), (1, 0, -3)]
        assert all_pairs(2, edges) is None


class TestRefusals:
    def test_an_edge_naming_a_missing_vertex_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs(2, [(0, 5, 1)])

    def test_an_empty_graph_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs(0, [])
