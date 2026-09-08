from __future__ import annotations

import pytest

from beacon.codel import CoDel
from beacon.errors import Invalid


class TestConstruction:
    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            CoDel(target_ms=0)


class TestGoodQueue:
    def test_a_brief_spike_does_not_drop(self):
        codel = CoDel(target_ms=5, interval_ms=100)
        # delay rises above target then drains before the interval
        assert not codel.observe(20, now_ms=0)
        assert not codel.observe(2, now_ms=50)
        assert not codel.is_standing()

    def test_a_below_target_queue_never_drops(self):
        codel = CoDel(target_ms=5, interval_ms=100)
        for tick in range(5):
            assert not codel.observe(1, now_ms=tick * 30)


class TestBadQueue:
    def test_a_persistent_backlog_triggers_a_drop(self):
        codel = CoDel(target_ms=5, interval_ms=100)
        assert not codel.observe(20, now_ms=0)
        assert not codel.observe(20, now_ms=50)
        assert codel.observe(20, now_ms=120)

    def test_the_timer_resets_when_the_queue_drains(self):
        codel = CoDel(target_ms=5, interval_ms=100)
        codel.observe(20, now_ms=0)
        codel.observe(1, now_ms=50)  # drained, resets
        assert not codel.observe(20, now_ms=60)  # timer restarts
        assert not codel.observe(20, now_ms=120)  # only 60ms in
