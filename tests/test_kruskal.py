from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.kruskal import minimum_spanning_tree


class TestMST:
    def test_it_builds_the_minimum_tree(self):
        nodes = {"a", "b", "c", "d"}
        edges = [
            (1, "a", "b"),
            (3, "a", "c"),
            (1, "b", "c"),
            (6, "c", "d"),
            (5, "b", "d"),
        ]
        tree, total = minimum_spanning_tree(nodes, edges)
        assert len(tree) == 3
        # a-b(1), b-c(1), b-d(5) = 7 beats using the 3 and 6 edges
        assert total == 7

    def test_it_avoids_cycles(self):
        nodes = {"a", "b", "c"}
        edges = [(1, "a", "b"), (1, "b", "c"), (1, "a", "c")]
        tree, _total = minimum_spanning_tree(nodes, edges)
        assert len(tree) == 2  # only two of the three edges

    def test_a_single_node_needs_no_edges(self):
        tree, total = minimum_spanning_tree({"a"}, [])
        assert tree == []
        assert total == 0


class TestDisconnected:
    def test_a_disconnected_graph_is_refused(self):
        with pytest.raises(Invalid) as caught:
            minimum_spanning_tree({"a", "b", "island"}, [(1, "a", "b")])
        assert "cannot be reached" in str(caught.value)
