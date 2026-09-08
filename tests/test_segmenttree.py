from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.segmenttree import SegmentTree


class TestRangeSum:
    def test_point_updates_reflect_in_range_sums(self):
        tree = SegmentTree(size=8)
        tree.update(0, 5)
        tree.update(3, 2)
        tree.update(7, 7)
        assert tree.range_sum(0, 8) == 14
        assert tree.range_sum(0, 4) == 7

    def test_a_half_open_range_excludes_the_upper_bound(self):
        tree = SegmentTree(size=4)
        for i in range(4):
            tree.update(i, i + 1)  # 1,2,3,4
        assert tree.range_sum(1, 3) == 2 + 3

    def test_updating_overwrites_a_leaf(self):
        tree = SegmentTree(size=4)
        tree.update(1, 10)
        tree.update(1, 3)  # overwrite, not add
        assert tree.range_sum(0, 4) == 3


class TestBounds:
    def test_an_out_of_range_index_is_refused(self):
        with pytest.raises(Invalid):
            SegmentTree(4).update(4, 1)

    def test_an_out_of_range_query_is_refused(self):
        with pytest.raises(Invalid):
            SegmentTree(4).range_sum(0, 9)

    def test_a_zero_size_is_refused(self):
        with pytest.raises(Invalid):
            SegmentTree(0)
