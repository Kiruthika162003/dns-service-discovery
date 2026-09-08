from __future__ import annotations

from beacon.transitiveclosure import closure, reaches

# a -> b -> c ; d -> c
GRAPH = {"a": {"b"}, "b": {"c"}, "c": set(), "d": {"c"}}


class TestClosure:
    def test_reachability_is_transitive(self):
        closed = closure(GRAPH)
        assert closed["a"] == {"b", "c"}

    def test_a_sink_reaches_nothing(self):
        closed = closure(GRAPH)
        assert closed["c"] == set()

    def test_direct_reach(self):
        closed = closure(GRAPH)
        assert "c" in closed["d"]


class TestReaches:
    def test_a_reaches_c_transitively(self):
        assert reaches(closure(GRAPH), "a", "c")

    def test_c_does_not_reach_a(self):
        assert not reaches(closure(GRAPH), "c", "a")

    def test_unrelated_nodes_do_not_reach(self):
        assert not reaches(closure(GRAPH), "a", "d")
