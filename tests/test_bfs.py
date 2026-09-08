from __future__ import annotations

from beacon.bfs import hop_distances, reachable

GRAPH = {
    "a": {"b", "c"},
    "b": {"d"},
    "c": {"d"},
    "d": {"e"},
    "e": set(),
}


class TestHopDistances:
    def test_it_measures_fewest_hops(self):
        dist = hop_distances(GRAPH, "a")
        assert dist["a"] == 0
        assert dist["b"] == 1
        assert dist["d"] == 2
        assert dist["e"] == 3

    def test_the_first_arrival_fixes_the_distance(self):
        # d is reachable via b or c, both at distance 2
        assert hop_distances(GRAPH, "a")["d"] == 2


class TestReachable:
    def test_it_finds_all_reachable_nodes(self):
        assert reachable(GRAPH, "a") == {"a", "b", "c", "d", "e"}

    def test_an_unreachable_node_is_excluded(self):
        graph = {"a": {"b"}, "b": set(), "island": set()}
        assert "island" not in reachable(graph, "a")

    def test_a_sink_reaches_only_itself(self):
        assert reachable(GRAPH, "e") == {"e"}
