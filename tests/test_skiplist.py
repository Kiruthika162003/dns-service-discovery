from __future__ import annotations

import random

import pytest

from beacon.errors import Invalid
from beacon.skiplist import SkipList


class TestOrdering:
    def test_keys_come_out_sorted(self):
        random.seed(1)
        sl = SkipList()
        for key in [5, 1, 8, 3, 9, 2, 7, 4, 6, 0]:
            sl.insert(key)
        assert sl.keys() == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_a_duplicate_insert_is_ignored(self):
        sl = SkipList()
        sl.insert(3)
        sl.insert(3)
        assert sl.keys() == [3]


class TestMembership:
    def test_inserted_keys_are_found(self):
        random.seed(2)
        sl = SkipList()
        for key in range(50):
            sl.insert(key)
        for key in range(50):
            assert sl.contains(key)

    def test_absent_keys_are_not_found(self):
        sl = SkipList()
        sl.insert(1)
        sl.insert(3)
        assert not sl.contains(2)
        assert not sl.contains(100)


class TestConstruction:
    def test_a_bad_probability_is_refused(self):
        with pytest.raises(Invalid):
            SkipList(probability=1.0)

    def test_a_zero_max_level_is_refused(self):
        with pytest.raises(Invalid):
            SkipList(max_level=0)
