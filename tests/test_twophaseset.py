from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.twophaseset import TwoPhaseSet


class TestMembership:
    def test_an_added_element_is_present(self):
        s = TwoPhaseSet()
        s.add("a")
        assert s.contains("a")

    def test_a_removed_element_is_absent(self):
        s = TwoPhaseSet()
        s.add("a")
        s.remove("a")
        assert not s.contains("a")


class TestPermanence:
    def test_a_tombstoned_element_cannot_be_re_added(self):
        s = TwoPhaseSet()
        s.add("a")
        s.remove("a")
        with pytest.raises(Invalid) as caught:
            s.add("a")
        assert "use an OR-set to re-add" in str(caught.value)

    def test_removing_a_never_added_element_is_refused(self):
        with pytest.raises(Invalid):
            TwoPhaseSet().remove("ghost")


class TestMerge:
    def test_a_tombstone_wins_across_a_merge(self):
        a = TwoPhaseSet()
        a.add("x")
        b = a.merge(TwoPhaseSet())
        b.remove("x")  # removed on one replica
        # merging the removal back means x is gone everywhere
        merged = a.merge(b)
        assert not merged.contains("x")
