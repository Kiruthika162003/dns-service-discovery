from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.fenwick import Fenwick


class TestPrefixSum:
    def test_updates_accumulate_into_prefixes(self):
        tree = Fenwick(size=8)
        tree.update(1, 5)
        tree.update(3, 2)
        tree.update(5, 7)
        assert tree.prefix_sum(5) == 14
        assert tree.prefix_sum(2) == 5

    def test_an_empty_tree_sums_zero(self):
        assert Fenwick(8).prefix_sum(8) == 0


class TestRangeSum:
    def test_a_range_is_the_difference_of_prefixes(self):
        tree = Fenwick(8)
        tree.update(2, 3)
        tree.update(4, 4)
        tree.update(6, 5)
        assert tree.range_sum(3, 6) == 9

    def test_a_reversed_range_is_refused(self):
        with pytest.raises(Invalid):
            Fenwick(8).range_sum(5, 2)


class TestBounds:
    def test_an_index_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            Fenwick(8).update(9, 1)

    def test_a_zero_size_is_refused(self):
        with pytest.raises(Invalid):
            Fenwick(0)
