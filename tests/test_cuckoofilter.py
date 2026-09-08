from __future__ import annotations

import pytest

from beacon.cuckoofilter import CuckooFilter
from beacon.errors import Invalid


class TestConstruction:
    def test_a_non_power_of_two_bucket_count_is_refused(self):
        with pytest.raises(Invalid):
            CuckooFilter(num_buckets=100)


class TestMembership:
    def test_added_items_are_present(self):
        cf = CuckooFilter(num_buckets=64, bucket_size=4)
        for i in range(20):
            assert cf.add(f"item-{i}")
        for i in range(20):
            assert cf.contains(f"item-{i}")

    def test_deletion_removes_an_item(self):
        cf = CuckooFilter(num_buckets=64, bucket_size=4)
        cf.add("gone")
        assert cf.contains("gone")
        assert cf.delete("gone")
        assert not cf.contains("gone")

    def test_deleting_an_absent_item_reports_false(self):
        cf = CuckooFilter(num_buckets=64, bucket_size=4)
        assert not cf.delete("never-added")


class TestFullness:
    def test_a_tiny_full_table_eventually_refuses_an_insert(self):
        cf = CuckooFilter(num_buckets=2, bucket_size=1, max_kicks=5)
        results = [cf.add(f"x-{i}") for i in range(20)]
        # a two-slot table cannot hold twenty; some insert must fail
        assert not all(results)
