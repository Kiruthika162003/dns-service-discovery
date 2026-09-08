from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.prim import minimum_spanning_tree


def graph() -> dict[str, dict[str, int]]:
    return {
        "a": {"b": 1, "c": 3},
        "b": {"a": 1, "c": 1, "d": 5},
        "c": {"a": 3, "b": 1, "d": 6},
        "d": {"b": 5, "c": 6},
    }


class TestMST:
    def test_it_builds_the_minimum_total(self):
        nodes = {"a", "b", "c", "d"}
        tree, total = minimum_spanning_tree(nodes, graph(), start="a")
        assert len(tree) == 3
        assert total == 7  # a-b(1), b-c(1), b-d(5)

    def test_a_single_node_needs_no_edges(self):
        tree, total = minimum_spanning_tree({"a"}, {"a": {}}, start="a")
        assert tree == []
        assert total == 0


class TestRefusals:
    def test_a_start_outside_the_nodes_is_refused(self):
        with pytest.raises(Invalid):
            minimum_spanning_tree({"a"}, {"a": {}}, start="z")

    def test_a_disconnected_graph_is_refused(self):
        nodes = {"a", "b", "island"}
        adjacency = {"a": {"b": 1}, "b": {"a": 1}, "island": {}}
        with pytest.raises(Invalid) as caught:
            minimum_spanning_tree(nodes, adjacency, start="a")
        assert "no spanning tree exists" in str(caught.value)
