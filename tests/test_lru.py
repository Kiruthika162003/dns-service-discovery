from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lru import LRUCache


class TestBasics:
    def test_a_stored_value_is_retrieved(self):
        cache = LRUCache(2)
        cache.put("a", "1")
        assert cache.get("a") == "1"

    def test_a_miss_returns_none(self):
        assert LRUCache(2).get("absent") is None

    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            LRUCache(0)


class TestEviction:
    def test_the_oldest_is_evicted_when_full(self):
        cache = LRUCache(2)
        cache.put("a", "1")
        cache.put("b", "2")
        cache.put("c", "3")
        assert cache.get("a") is None
        assert cache.last_evicted == "a"

    def test_a_hit_promotes_and_spares_an_entry(self):
        cache = LRUCache(2)
        cache.put("a", "1")
        cache.put("b", "2")
        cache.get("a")  # a is now most recent
        cache.put("c", "3")
        assert cache.get("a") == "1"
        assert cache.get("b") is None


class TestScanWeakness:
    def test_a_scan_evicts_the_hot_set(self):
        cache = LRUCache(3)
        for hot in ("h1", "h2", "h3"):
            cache.put(hot, hot)
        # a scan of cold keys walks the hot set out
        for cold in ("s1", "s2", "s3"):
            cache.put(cold, cold)
        assert all(cache.get(hot) is None for hot in ("h1", "h2", "h3"))
