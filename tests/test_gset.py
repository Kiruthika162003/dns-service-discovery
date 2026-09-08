from __future__ import annotations

from beacon.gset import GSet


class TestBasics:
    def test_an_added_element_is_present(self):
        s = GSet()
        s.add("a")
        assert s.contains("a")

    def test_an_absent_element_is_not(self):
        assert not GSet().contains("x")


class TestMerge:
    def test_merge_is_the_union(self):
        a = GSet()
        a.add("x")
        b = GSet()
        b.add("y")
        assert a.merge(b).as_set() == {"x", "y"}

    def test_merge_is_commutative(self):
        a = GSet()
        a.add("x")
        b = GSet()
        b.add("y")
        assert a.merge(b).as_set() == b.merge(a).as_set()

    def test_merge_is_idempotent(self):
        a = GSet()
        a.add("x")
        assert a.merge(a).as_set() == {"x"}

    def test_convergence_regardless_of_order(self):
        a = GSet()
        a.add("1")
        a.add("2")
        b = GSet()
        b.add("2")
        b.add("3")
        assert a.merge(b).as_set() == {"1", "2", "3"}
