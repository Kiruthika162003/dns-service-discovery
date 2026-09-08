from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.slidinglog import SlidingLog


class TestConstruction:
    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            SlidingLog(window=0, limit=5)

    def test_a_zero_limit_is_refused(self):
        with pytest.raises(Invalid):
            SlidingLog(window=10, limit=0)


class TestExactness:
    def test_it_admits_up_to_the_limit(self):
        log = SlidingLog(window=10, limit=3)
        assert log.allow(now=0)
        assert log.allow(now=1)
        assert log.allow(now=2)
        assert not log.allow(now=3)

    def test_aged_requests_free_up_room(self):
        log = SlidingLog(window=10, limit=2)
        log.allow(now=0)
        log.allow(now=1)
        assert not log.allow(now=5)
        # the request at 0 ages out at now=11
        assert log.allow(now=11)

    def test_no_boundary_double_burst(self):
        log = SlidingLog(window=10, limit=3)
        # fill at the end of a nominal window
        for tick in (8, 9, 10):
            assert log.allow(now=tick)
        # a burst right after cannot exceed the true trailing count
        assert not log.allow(now=11)


class TestOccupancy:
    def test_occupancy_reflects_the_trailing_window(self):
        log = SlidingLog(window=10, limit=5)
        log.allow(now=0)
        log.allow(now=1)
        assert log.occupancy(now=5) == 2
        assert log.occupancy(now=20) == 0
