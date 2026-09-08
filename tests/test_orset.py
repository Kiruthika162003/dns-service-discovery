from __future__ import annotations

from beacon.orset import ORSet


class TestBasics:
    def test_an_added_element_is_present(self):
        chosen = ORSet()
        chosen.add("web", "t1")
        assert chosen.contains("web")

    def test_a_remove_tombstones_the_observed_tags(self):
        chosen = ORSet()
        chosen.add("web", "t1")
        chosen.remove("web")
        assert not chosen.contains("web")


class TestAddWins:
    def test_a_concurrent_add_beats_a_remove(self):
        left = ORSet()
        left.add("web", "t1")
        right = left.merge(ORSet())
        # right removes the tag it saw
        right.remove("web")
        # left concurrently adds a new tag the remove never saw
        left.add("web", "t2")
        merged = left.merge(right)
        assert merged.contains("web")

    def test_the_merge_is_order_independent(self):
        left = ORSet()
        left.add("web", "t1")
        left.add("web", "t2")
        right = ORSet()
        right.add("web", "t1")
        right.remove("web")
        assert left.merge(right).contains("web") == (
            right.merge(left).contains("web")
        )


class TestElements:
    def test_elements_lists_the_live_members(self):
        chosen = ORSet()
        chosen.add("a", "t1")
        chosen.add("b", "t2")
        chosen.remove("b")
        assert chosen.elements() == {"a"}

    def test_merge_is_idempotent(self):
        chosen = ORSet()
        chosen.add("a", "t1")
        assert chosen.merge(chosen).elements() == {"a"}
