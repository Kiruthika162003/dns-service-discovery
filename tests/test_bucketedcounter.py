from __future__ import annotations

import pytest

from beacon.bucketedcounter import BucketedCounter
from beacon.errors import Invalid


class TestCounting:
    def test_recent_events_are_counted(self):
        counter = BucketedCounter(window=60, bucket_width=10)
        counter.record(now=0)
        counter.record(now=5)
        counter.record(now=12)
        assert counter.count(now=12) == 3

    def test_aged_events_fall_out_of_the_window(self):
        counter = BucketedCounter(window=60, bucket_width=10)
        counter.record(now=0)
        counter.record(now=5)
        # far in the future, the old bucket has aged out
        assert counter.count(now=200) == 0

    def test_the_window_edge_keeps_recent_buckets(self):
        counter = BucketedCounter(window=60, bucket_width=10)
        counter.record(now=10)
        counter.record(now=50)
        assert counter.count(now=60) == 2


class TestConstruction:
    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            BucketedCounter(window=0, bucket_width=10)

    def test_a_bucket_wider_than_the_window_is_refused(self):
        with pytest.raises(Invalid):
            BucketedCounter(window=10, bucket_width=60)
