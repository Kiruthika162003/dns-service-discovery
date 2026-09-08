from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.versionvector import (
    compare,
    descends_from,
    increment,
    is_conflict,
    merge,
)


class TestCompare:
    def test_equal_vectors(self):
        assert compare({"a": 1}, {"a": 1}) == "equal"

    def test_a_strict_descendant_dominates(self):
        assert compare({"a": 2, "b": 1}, {"a": 1, "b": 1}) == (
            "left-dominates"
        )

    def test_independent_edits_are_concurrent(self):
        assert compare({"a": 2, "b": 1}, {"a": 1, "b": 2}) == (
            "concurrent"
        )


class TestIncrementAndMerge:
    def test_increment_bumps_only_the_editor(self):
        assert increment({"a": 1, "b": 3}, "a") == {"a": 2, "b": 3}

    def test_merge_takes_the_entrywise_max(self):
        assert merge({"a": 2, "b": 1}, {"a": 1, "b": 5}) == {
            "a": 2,
            "b": 5,
        }

    def test_a_merge_settles_the_conflict(self):
        left = {"a": 2, "b": 1}
        right = {"a": 1, "b": 2}
        assert is_conflict(left, right)
        merged = merge(left, right)
        assert not is_conflict(merged, left)
        assert not is_conflict(merged, right)


class TestLineage:
    def test_descends_from_holds_for_a_descendant(self):
        assert descends_from({"a": 2}, {"a": 1})

    def test_concurrent_vectors_have_no_lineage(self):
        with pytest.raises(Invalid) as caught:
            descends_from({"a": 2, "b": 1}, {"a": 1, "b": 2})
        assert "conflict, not a lineage" in str(caught.value)
