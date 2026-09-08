from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ttlwheel import TimingWheel


class TestScheduling:
    def test_an_entry_expires_at_its_tick(self):
        wheel = TimingWheel(size=8)
        wheel.schedule("a", delay=3)
        assert wheel.advance() == []  # tick 1
        assert wheel.advance() == []  # tick 2
        assert wheel.advance() == ["a"]  # tick 3

    def test_a_delay_beyond_one_revolution_still_waits(self):
        wheel = TimingWheel(size=4)
        wheel.schedule("far", delay=6)  # same slot as tick 2, but round 1
        results = [wheel.advance() for _ in range(6)]
        # it must not fire at tick 2, only at tick 6
        assert results[1] == []
        assert results[5] == ["far"]

    def test_several_entries_in_one_tick_all_fire(self):
        wheel = TimingWheel(size=8)
        wheel.schedule("a", delay=2)
        wheel.schedule("b", delay=2)
        wheel.advance()
        assert sorted(wheel.advance()) == ["a", "b"]


class TestRefusals:
    def test_a_zero_size_wheel_is_refused(self):
        with pytest.raises(Invalid):
            TimingWheel(0)

    def test_a_nonpositive_delay_is_refused(self):
        with pytest.raises(Invalid):
            TimingWheel(8).schedule("a", delay=0)
