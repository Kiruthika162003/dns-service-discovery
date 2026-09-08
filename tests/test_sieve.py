from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.sieve import Sieve


class TestConstruction:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            Sieve(0)


class TestReprieve:
    def test_a_visited_entry_is_spared_and_an_unvisited_older_one_goes(self):
        cache = Sieve(capacity=3)
        for key in ("a", "b", "c"):
            cache.access(key)
        cache.access("a")  # a earns a reprieve
        cache.access("d")  # eviction: a is cleared and spared, b evicted
        resident = cache.resident()
        assert "a" in resident
        assert "b" not in resident
        assert "d" in resident
        assert cache.last_evicted == "b"


class TestScanResistance:
    def test_an_unvisited_newcomer_is_evicted_quickly(self):
        cache = Sieve(capacity=2)
        cache.access("a")
        cache.access("b")
        cache.access("a")  # a revisited
        # c arrives: b (unvisited, at the hand) should go, a spared
        cache.access("c")
        assert "a" in cache.resident()
        assert "b" not in cache.resident()


class TestBounds:
    def test_the_cache_never_exceeds_capacity(self):
        cache = Sieve(capacity=3)
        for key in "abcdefgh":
            cache.access(key)
        assert len(cache.resident()) <= 3
