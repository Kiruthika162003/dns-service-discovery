from __future__ import annotations

from beacon.connectedcomponents import components, same_component


class TestComponents:
    def test_two_islands_are_found(self):
        graph = {"a": {"b"}, "b": {"c"}, "x": {"y"}}
        found = components(graph)
        assert len(found) == 2
        sizes = sorted(len(c) for c in found)
        assert sizes == [2, 3]

    def test_edges_are_treated_as_undirected(self):
        # only a->b given; b should still reach a
        graph = {"a": {"b"}}
        assert same_component(graph, "b", "a")

    def test_a_lone_node_is_its_own_component(self):
        graph = {"a": {"b"}, "loner": set()}
        assert any(c == {"loner"} for c in components(graph))


class TestSameComponent:
    def test_connected_nodes_share_a_component(self):
        graph = {"a": {"b"}, "b": {"c"}}
        assert same_component(graph, "a", "c")

    def test_disconnected_nodes_do_not(self):
        graph = {"a": {"b"}, "x": {"y"}}
        assert not same_component(graph, "a", "x")
