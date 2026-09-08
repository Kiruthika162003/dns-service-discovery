from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lfu import LFUCache


class TestBasics:
    def test_a_stored_value_is_retrieved(self):
        cache = LFUCache(2)
        cache.put("a", "1")
        assert cache.get("a") == "1"

    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            LFUCache(0)


class TestFrequencyEviction:
    def test_the_least_frequent_is_evicted(self):
        cache = LFUCache(2)
        cache.put("a", "1")
        cache.put("b", "2")
        cache.get("a")  # a freq 2, b freq 1
        cache.put("c", "3")  # evicts b
        assert cache.get("b") is None
        assert cache.get("a") == "1"
        assert cache.last_evicted == "b"


class TestScanResistance:
    def test_a_hot_key_survives_a_scan(self):
        cache = LFUCache(2)
        cache.put("hot", "h")
        for _ in range(5):
            cache.get("hot")  # build frequency
        cache.put("s1", "1")  # fills to capacity
        cache.put("s2", "2")  # evicts s1 (freq 1), not hot
        assert cache.get("hot") == "h"
        assert cache.get("s1") is None


class TestStaleFavorite:
    def test_a_once_popular_key_clings(self):
        cache = LFUCache(2)
        cache.put("old", "o")
        for _ in range(10):
            cache.get("old")  # very high frequency, now cold
        cache.put("new1", "1")
        cache.put("new2", "2")  # evicts new1, old squats on
        assert cache.get("old") == "o"
