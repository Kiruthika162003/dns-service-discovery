from __future__ import annotations

import pytest

from beacon.connectionpool import ConnectionPool
from beacon.errors import Invalid, Refused


class TestConstruction:
    def test_a_zero_cap_is_refused(self):
        with pytest.raises(Invalid):
            ConnectionPool(max_total=0)

    def test_an_idle_floor_above_the_cap_is_refused(self):
        with pytest.raises(Invalid):
            ConnectionPool(max_total=2, min_idle=3)


class TestAcquire:
    def test_it_creates_up_to_the_cap(self):
        pool = ConnectionPool(max_total=2)
        assert pool.acquire() == "created"
        assert pool.acquire() == "created"

    def test_past_the_cap_it_refuses(self):
        pool = ConnectionPool(max_total=1)
        pool.acquire()
        with pytest.raises(Refused) as caught:
            pool.acquire()
        assert "exhausting the backend" in str(caught.value)

    def test_an_idle_connection_is_reused(self):
        pool = ConnectionPool(max_total=2, min_idle=1)
        pool.acquire()
        pool.release()  # returns to idle
        assert pool.acquire() == "reused"


class TestRelease:
    def test_release_keeps_the_idle_floor_warm(self):
        pool = ConnectionPool(max_total=3, min_idle=1)
        pool.acquire()
        assert pool.release() == "returned-idle"

    def test_release_over_the_floor_closes(self):
        pool = ConnectionPool(max_total=3, min_idle=0)
        pool.acquire()
        assert pool.release() == "closed"

    def test_a_double_release_is_refused(self):
        pool = ConnectionPool(max_total=2)
        with pytest.raises(Invalid):
            pool.release()
