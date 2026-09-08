from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.intervalmerge import covers, merge, total_length


class TestMerge:
    def test_overlapping_intervals_coalesce(self):
        assert merge([(1, 5), (3, 8), (10, 12)]) == [(1, 8), (10, 12)]

    def test_touching_intervals_join(self):
        assert merge([(1, 5), (5, 9)]) == [(1, 9)]

    def test_disjoint_intervals_are_kept(self):
        assert merge([(10, 12), (1, 3)]) == [(1, 3), (10, 12)]

    def test_an_empty_set_merges_to_nothing(self):
        assert merge([]) == []

    def test_a_backwards_interval_is_refused(self):
        with pytest.raises(Invalid):
            merge([(5, 1)])


class TestQueries:
    def test_coverage_uses_the_merged_form(self):
        merged = merge([(1, 5), (3, 8)])
        assert covers(merged, 4)
        assert not covers(merged, 9)

    def test_total_length_sums_the_disjoint_cover(self):
        merged = merge([(1, 5), (3, 8), (10, 12)])
        # (1,8) length 7 + (10,12) length 2 = 9
        assert total_length(merged) == 9
