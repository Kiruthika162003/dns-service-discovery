from __future__ import annotations

import pytest

from beacon.arc import ARC
from beacon.errors import Invalid


class TestConstruction:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            ARC(0)


class TestBounds:
    def test_the_live_cache_never_exceeds_capacity(self):
        arc = ARC(3)
        for key in "abcdefghij":
            arc.access(key)
        assert len(arc.resident()) <= 3


class TestFrequencyProtection:
    def test_a_repeatedly_used_key_survives_a_scan(self):
        arc = ARC(4)
        for _ in range(3):
            arc.access("h1")
            arc.access("h2")
        for cold in ("s1", "s2", "s3", "s4", "s5", "s6"):
            arc.access(cold)
        assert "h1" in arc.resident()
        assert "h2" in arc.resident()


class TestAdaptation:
    def test_a_recency_ghost_hit_grows_the_target(self):
        arc = ARC(2)
        arc.access("a")
        arc.access("a")  # a -> T2 (frequent)
        arc.access("b")
        arc.access("c")  # evicts b into the B1 ghost list
        assert arc.p == 0
        arc.access("b")  # ghost hit in B1: bias toward recency
        assert arc.p > 0
