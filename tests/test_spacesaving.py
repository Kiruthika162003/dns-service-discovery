from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.spacesaving import SpaceSaving


class TestHeavyHitters:
    def test_a_dominant_item_is_never_evicted(self):
        summary = SpaceSaving(capacity=3)
        for _ in range(100):
            summary.offer("heavy")
        for i in range(50):
            summary.offer(f"cold-{i}")
        assert summary.estimate("heavy") >= 100

    def test_the_top_lists_the_dominant_items(self):
        summary = SpaceSaving(capacity=3)
        for _ in range(30):
            summary.offer("a")
        for _ in range(20):
            summary.offer("b")
        for _ in range(5):
            summary.offer("c")
        top = summary.top(2)
        assert [item for item, _ in top] == ["a", "b"]


class TestOverestimateIsOneSided:
    def test_a_light_item_can_inherit_an_inflated_count(self):
        summary = SpaceSaving(capacity=2)
        summary.offer("a")  # a:1
        summary.offer("b")  # b:1
        summary.offer("c")  # evicts min, c inherits 1 -> c:2
        # c was seen once but its estimate is an overcount, never under
        assert summary.estimate("c") >= 1


class TestConstruction:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            SpaceSaving(0)
