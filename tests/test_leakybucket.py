from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.leakybucket import LeakyBucket


class TestConstruction:
    def test_a_zero_leak_rate_is_refused(self):
        with pytest.raises(Invalid):
            LeakyBucket(leak_rate=0, capacity=10)

    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            LeakyBucket(leak_rate=1, capacity=0)


class TestShaping:
    def test_it_accepts_up_to_capacity(self):
        bucket = LeakyBucket(leak_rate=1, capacity=3)
        assert bucket.offer()
        assert bucket.offer()
        assert bucket.offer()
        assert not bucket.offer()

    def test_draining_makes_room_again(self):
        bucket = LeakyBucket(leak_rate=1, capacity=3)
        for _ in range(3):
            bucket.offer()
        assert not bucket.offer()
        bucket.drain(2.0)  # level 3 -> 1
        assert bucket.offer()

    def test_draining_never_goes_negative(self):
        bucket = LeakyBucket(leak_rate=5, capacity=3)
        bucket.offer()
        bucket.drain(10.0)
        assert bucket.level == 0.0

    def test_a_full_bucket_reports_overflowing(self):
        bucket = LeakyBucket(leak_rate=1, capacity=2)
        bucket.offer()
        bucket.offer()
        assert bucket.overflowing()
