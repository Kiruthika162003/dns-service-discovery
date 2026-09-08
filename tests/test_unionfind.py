from __future__ import annotations

from beacon.unionfind import UnionFind


class TestConnectivity:
    def test_unmerged_nodes_are_separate(self):
        uf = UnionFind()
        assert not uf.connected("a", "b")

    def test_a_union_connects_two_nodes(self):
        uf = UnionFind()
        uf.union("a", "b")
        assert uf.connected("a", "b")

    def test_connectivity_is_transitive(self):
        uf = UnionFind()
        uf.union("a", "b")
        uf.union("b", "c")
        assert uf.connected("a", "c")


class TestComponents:
    def test_the_component_count_falls_as_sets_merge(self):
        uf = UnionFind()
        for node in ("a", "b", "c", "d"):
            uf.find(node)  # introduce as singletons
        assert uf.components() == 4
        uf.union("a", "b")
        uf.union("c", "d")
        assert uf.components() == 2
        uf.union("b", "c")
        assert uf.components() == 1

    def test_a_redundant_union_changes_nothing(self):
        uf = UnionFind()
        uf.union("a", "b")
        before = uf.components()
        uf.union("a", "b")
        assert uf.components() == before


class TestPathCompression:
    def test_find_returns_a_stable_root(self):
        uf = UnionFind()
        uf.union("a", "b")
        uf.union("b", "c")
        assert uf.find("a") == uf.find("c")
