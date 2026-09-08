from __future__ import annotations

import pytest

from beacon.clocksweep import Clock
from beacon.errors import Invalid


class TestBasics:
    def test_it_fills_to_capacity(self):
        clock = Clock(capacity=3)
        for key in ("a", "b", "c"):
            clock.access(key)
        assert clock.resident() == {"a", "b", "c"}

    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            Clock(0)


class TestSecondChance:
    def test_a_retouched_entry_survives_the_next_eviction(self):
        clock = Clock(capacity=3)
        for key in ("a", "b", "c"):
            clock.access(key)
        clock.access("d")  # first eviction sweeps and drops a
        assert "a" not in clock.resident()
        clock.access("b")  # give b a second chance
        clock.access("e")  # eviction: b survives, c drops
        resident = clock.resident()
        assert "b" in resident
        assert "c" not in resident
        assert "e" in resident

    def test_the_last_evicted_is_recorded(self):
        clock = Clock(capacity=2)
        clock.access("a")
        clock.access("b")
        clock.access("c")
        assert clock.last_evicted == "a"
