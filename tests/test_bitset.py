from __future__ import annotations

import pytest

from beacon.bitset import BitSet
from beacon.errors import Invalid


class TestMembership:
    def test_an_added_member_is_present(self):
        s = BitSet()
        s.add(3)
        s.add(7)
        assert s.contains(3)
        assert s.contains(7)
        assert not s.contains(4)

    def test_a_negative_member_is_refused(self):
        with pytest.raises(Invalid):
            BitSet().add(-1)

    def test_the_count_is_the_number_of_members(self):
        s = BitSet()
        for member in (1, 2, 40, 100):
            s.add(member)
        assert s.count() == 4


class TestOperations:
    def build(self, members: list[int]) -> BitSet:
        s = BitSet()
        for member in members:
            s.add(member)
        return s

    def test_union(self):
        a = self.build([1, 2, 3])
        b = self.build([3, 4, 5])
        assert a.union(b).members() == [1, 2, 3, 4, 5]

    def test_intersection(self):
        a = self.build([1, 2, 3])
        b = self.build([2, 3, 4])
        assert a.intersection(b).members() == [2, 3]

    def test_difference(self):
        a = self.build([1, 2, 3])
        b = self.build([2])
        assert a.difference(b).members() == [1, 3]


class TestMembers:
    def test_members_are_listed_ascending(self):
        s = BitSet()
        for member in (10, 1, 5):
            s.add(member)
        assert s.members() == [1, 5, 10]
