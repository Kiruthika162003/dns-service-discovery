from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.priorityqueue import effective_priority, next_item


class TestEffectivePriority:
    def test_waiting_raises_the_effective_priority(self):
        assert effective_priority(base=1, waited=100, aging_rate=0.1) == 11

    def test_a_negative_aging_rate_is_refused(self):
        with pytest.raises(Invalid):
            effective_priority(1, 100, aging_rate=-0.1)


class TestNextItem:
    def test_the_highest_base_wins_when_fresh(self):
        items = [("low", 1, 0), ("high", 10, 0)]
        assert next_item(items, aging_rate=0.1) == "high"

    def test_a_long_waiting_low_item_eventually_wins(self):
        # low base 1 waited 200 -> 1 + 20 = 21 beats high base 10 fresh
        items = [("low", 1, 200), ("high", 10, 0)]
        assert next_item(items, aging_rate=0.1) == "low"

    def test_an_empty_queue_is_refused(self):
        with pytest.raises(Invalid):
            next_item([], aging_rate=0.1)
