from __future__ import annotations

from beacon.eulerian import has_eulerian_circuit, has_eulerian_path


class TestCircuit:
    def test_a_triangle_has_a_circuit(self):
        tri = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
        assert has_eulerian_circuit(tri)

    def test_a_path_graph_has_no_circuit(self):
        path = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
        assert not has_eulerian_circuit(path)


class TestPath:
    def test_two_odd_vertices_give_a_path(self):
        path = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
        assert has_eulerian_path(path)

    def test_a_circuit_is_also_a_path(self):
        tri = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
        assert has_eulerian_path(tri)

    def test_four_odd_vertices_have_neither(self):
        star = {"c": {"x", "y", "z"}, "x": {"c"}, "y": {"c"}, "z": {"c"}}
        assert not has_eulerian_path(star)


class TestConnectivity:
    def test_a_disconnected_graph_has_no_path(self):
        disc = {"a": {"b"}, "b": {"a"}, "x": {"y"}, "y": {"x"}}
        assert not has_eulerian_path(disc)
