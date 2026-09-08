from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.prefixsum import PrefixSum


class TestRangeSum:
    def test_it_sums_a_range_in_constant_time(self):
        ps = PrefixSum([5, 2, 8, 1, 9, 4])
        assert ps.range_sum(1, 4) == 2 + 8 + 1
        assert ps.range_sum(0, 6) == 29

    def test_a_half_open_range_excludes_the_upper_bound(self):
        ps = PrefixSum([1, 2, 3, 4])
        assert ps.range_sum(1, 3) == 2 + 3

    def test_an_empty_range_is_zero(self):
        ps = PrefixSum([1, 2, 3])
        assert ps.range_sum(2, 2) == 0

    def test_the_total(self):
        assert PrefixSum([1, 2, 3, 4]).total() == 10


class TestBounds:
    def test_an_out_of_range_query_is_refused(self):
        with pytest.raises(Invalid):
            PrefixSum([1, 2, 3]).range_sum(0, 9)
