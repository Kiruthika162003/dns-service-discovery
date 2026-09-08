from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.quickselect import kth_smallest, percentile


class TestKthSmallest:
    def test_it_finds_order_statistics(self):
        data = [7, 2, 9, 1, 5, 8, 3]
        assert kth_smallest(data, 1) == 1
        assert kth_smallest(data, 4) == 5
        assert kth_smallest(data, 7) == 9

    def test_it_matches_a_sort(self):
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        ordered = sorted(data)
        for k in range(1, len(data) + 1):
            assert kth_smallest(data, k) == ordered[k - 1]

    def test_it_handles_duplicates(self):
        data = [4, 4, 4, 1, 4]
        assert kth_smallest(data, 1) == 1
        assert kth_smallest(data, 2) == 4

    def test_a_rank_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            kth_smallest([1, 2, 3], 5)


class TestPercentile:
    def test_the_median(self):
        assert percentile([1, 2, 3, 4, 5], 0.5) == 3

    def test_a_high_percentile(self):
        data = list(range(1, 101))  # 1..100
        assert percentile(data, 0.99) == 99

    def test_a_bad_fraction_is_refused(self):
        with pytest.raises(Invalid):
            percentile([1, 2, 3], 1.5)
