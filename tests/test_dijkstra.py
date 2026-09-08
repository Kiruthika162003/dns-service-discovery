from __future__ import annotations

import pytest

from beacon.dijkstra import shortest_paths
from beacon.errors import Invalid

GRAPH = {
    "a": {"b": 1, "c": 4},
    "b": {"c": 2, "d": 5},
    "c": {"d": 1},
    "d": {},
}


class TestShortestPaths:
    def test_it_finds_the_least_latency_distances(self):
        dist = shortest_paths(GRAPH, "a")
        assert dist["a"] == 0
        assert dist["b"] == 1
        assert dist["c"] == 3  # a->b->c beats a->c
        assert dist["d"] == 4  # a->b->c->d

    def test_an_unreachable_node_is_absent(self):
        graph = {"a": {"b": 1}, "b": {}, "island": {}}
        dist = shortest_paths(graph, "a")
        assert "island" not in dist

    def test_the_source_is_zero(self):
        assert shortest_paths(GRAPH, "d") == {"d": 0}


class TestRefusals:
    def test_a_negative_edge_is_refused(self):
        with pytest.raises(Invalid) as caught:
            shortest_paths({"a": {"b": -1}, "b": {}}, "a")
        assert "Bellman-Ford" in str(caught.value)
