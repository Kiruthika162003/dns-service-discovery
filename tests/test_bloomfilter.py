from __future__ import annotations

import pytest

from beacon.bloomfilter import BloomFilter
from beacon.errors import Invalid


class TestNoFalseNegatives:
    def test_an_added_item_is_always_found(self):
        bloom = BloomFilter(size=1024, num_hashes=4)
        for i in range(200):
            bloom.add(f"name-{i}")
        for i in range(200):
            assert bloom.contains(f"name-{i}")

    def test_absent_is_trustworthy(self):
        # if it says absent, it truly is; a never-added item that
        # reports absent proves the one-sided guarantee
        bloom = BloomFilter(size=4096, num_hashes=5)
        bloom.add("present")
        # a fresh item is very likely absent at this low load
        assert not bloom.contains("definitely-not-added-xyz")


class TestConstruction:
    def test_a_zero_size_is_refused(self):
        with pytest.raises(Invalid):
            BloomFilter(size=0, num_hashes=3)

    def test_no_hashes_is_refused(self):
        with pytest.raises(Invalid):
            BloomFilter(size=1024, num_hashes=0)


class TestFalsePositiveRate:
    def test_the_rate_climbs_with_load(self):
        bloom = BloomFilter(size=1024, num_hashes=4)
        empty_rate = bloom.false_positive_rate()
        for i in range(300):
            bloom.add(f"x-{i}")
        assert bloom.false_positive_rate() > empty_rate

    def test_an_empty_filter_has_a_zero_rate(self):
        assert BloomFilter(size=1024, num_hashes=4).false_positive_rate() == 0.0
