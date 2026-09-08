from __future__ import annotations

import pytest

from beacon.countdownlatch import CountdownLatch
from beacon.errors import Invalid


class TestCountdown:
    def test_it_opens_when_the_count_reaches_zero(self):
        latch = CountdownLatch(count=3)
        latch.count_down()
        latch.count_down()
        assert not latch.ready()
        latch.count_down()
        assert latch.ready()

    def test_a_stray_extra_event_does_not_go_below_zero(self):
        latch = CountdownLatch(count=1)
        latch.count_down()
        latch.count_down()  # extra
        assert latch.remaining == 0
        assert latch.ready()

    def test_once_open_it_stays_open(self):
        latch = CountdownLatch(count=1)
        latch.count_down()
        assert latch.ready()
        # no operation reopens it; it is one-shot
        assert latch.remaining == 0


class TestConstruction:
    def test_a_zero_count_is_refused(self):
        with pytest.raises(Invalid):
            CountdownLatch(0)
