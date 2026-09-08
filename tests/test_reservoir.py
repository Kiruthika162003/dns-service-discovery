from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.reservoir import Reservoir


class TestFilling:
    def test_the_first_k_items_fill_the_reservoir(self):
        res = Reservoir(capacity=3)
        for item in ("a", "b", "c"):
            res.offer(item, draw=0.0)
        assert res.contents() == ["a", "b", "c"]

    def test_the_count_tracks_every_offer(self):
        res = Reservoir(capacity=2)
        for item in ("a", "b", "c", "d"):
            res.offer(item, draw=0.99)
        assert res.seen == 4


class TestReplacement:
    def test_a_low_draw_replaces_an_early_slot(self):
        res = Reservoir(capacity=3)
        for item in ("a", "b", "c"):
            res.offer(item, draw=0.0)
        # 4th item, draw 0.0 -> index 0 replaced
        res.offer("d", draw=0.0)
        assert res.contents()[0] == "d"

    def test_a_high_draw_keeps_the_reservoir(self):
        res = Reservoir(capacity=3)
        for item in ("a", "b", "c"):
            res.offer(item, draw=0.0)
        # 4th item, draw 0.99 -> index 3 (>= capacity), no replace
        res.offer("d", draw=0.99)
        assert "d" not in res.contents()


class TestRefusals:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            Reservoir(0)

    def test_a_draw_outside_the_unit_interval_is_refused(self):
        with pytest.raises(Invalid):
            Reservoir(2).offer("a", draw=1.0)
