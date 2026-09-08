from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.jumphash import (
    jump_hash,
    moved_fraction,
    remove_middle_bucket,
)

KEYS = [f"key-{i}" for i in range(5000)]


class TestMapping:
    def test_the_bucket_is_in_range(self):
        for key in KEYS[:100]:
            assert 0 <= jump_hash(key, 8) < 8

    def test_the_mapping_is_stable(self):
        assert jump_hash("key-1", 8) == jump_hash("key-1", 8)

    def test_a_single_bucket_takes_everything(self):
        assert all(jump_hash(key, 1) == 0 for key in KEYS[:50])

    def test_zero_buckets_is_refused(self):
        with pytest.raises(Invalid):
            jump_hash("key-1", 0)


class TestMinimalMovement:
    def test_growing_moves_about_one_in_n(self):
        fraction = moved_fraction(KEYS, 8, 9)
        assert 0.06 < fraction < 0.16

    def test_the_distribution_is_close_to_even(self):
        counts = [0] * 8
        for key in KEYS:
            counts[jump_hash(key, 8)] += 1
        average = len(KEYS) / 8
        assert max(counts) < average * 1.2
        assert min(counts) > average * 0.8


class TestTheConstraint:
    def test_removing_a_middle_bucket_is_refused(self):
        with pytest.raises(Invalid) as caught:
            remove_middle_bucket(3, 8)
        assert "only shed the top bucket" in str(caught.value)

    def test_removing_the_top_bucket_is_allowed(self):
        assert remove_middle_bucket(7, 8) is None
