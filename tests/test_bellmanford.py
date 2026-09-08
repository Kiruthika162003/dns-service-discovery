from __future__ import annotations

import pytest

from beacon.bellmanford import shortest_paths
from beacon.errors import Invalid


class TestShortestPaths:
    def test_the_classic_graph_with_a_negative_edge(self):
        edges = [
            (0, 1, 6), (0, 2, 7), (1, 2, 8), (1, 3, 5), (1, 4, -4),
            (2, 3, -3), (2, 4, 9), (3, 1, -2), (4, 0, 2), (4, 3, 7),
        ]
        assert shortest_paths(5, edges, 0) == [0, 2, 7, 4, -2]

    def test_an_unreachable_vertex_stays_at_infinity(self):
        distance = shortest_paths(3, [(0, 1, 5)], 0)
        assert distance[2] == float("inf")

    def test_the_source_is_at_distance_zero(self):
        assert shortest_paths(2, [(0, 1, 3)], 0)[0] == 0


class TestNegativeCycle:
    def test_a_reachable_negative_cycle_is_reported(self):
        edges = [(0, 1, 1), (1, 2, -3), (2, 0, 1)]
        assert shortest_paths(3, edges, 0) is None


class TestRefusals:
    def test_a_source_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            shortest_paths(3, [], 5)

    def test_an_edge_naming_a_missing_vertex_is_refused(self):
        with pytest.raises(Invalid):
            shortest_paths(2, [(0, 9, 1)], 0)

    def test_an_empty_graph_is_refused(self):
        with pytest.raises(Invalid):
            shortest_paths(0, [], 0)
