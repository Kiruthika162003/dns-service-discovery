from __future__ import annotations

from beacon.bipartite import is_bipartite


class TestBipartite:
    def test_an_even_cycle_is_bipartite(self):
        # square: a-b-c-d-a
        graph = {"a": {"b", "d"}, "b": {"c"}, "c": {"d"}, "d": set()}
        assert is_bipartite(graph)

    def test_an_odd_cycle_is_not(self):
        # triangle: a-b-c-a
        graph = {"a": {"b", "c"}, "b": {"c"}, "c": set()}
        assert not is_bipartite(graph)

    def test_a_tree_is_bipartite(self):
        graph = {"root": {"l", "r"}, "l": {"ll"}, "r": set(), "ll": set()}
        assert is_bipartite(graph)

    def test_disconnected_components_are_each_checked(self):
        graph = {"a": {"b"}, "x": {"y", "z"}, "y": {"z"}}
        # the x-y-z triangle makes it non-bipartite
        assert not is_bipartite(graph)

    def test_an_empty_graph_is_bipartite(self):
        assert is_bipartite({})
