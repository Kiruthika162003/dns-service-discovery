from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.partitions import PartitionSide, merge_partitions


def split() -> tuple[PartitionSide, PartitionSide]:
    east = PartitionSide(name="east")
    west = PartitionSide(name="west")
    for side in (east, west):
        side.write("billing/b1", "10.0.0.1:80", version=5)
    return east, west


class TestTheMerge:
    def test_one_sided_writes_carry_over_untouched(self):
        east, west = split()
        east.write("search/s1", "10.0.1.1:80", version=1)
        merged, report = merge_partitions(east, west)
        assert merged["search/s1"] == ("10.0.1.1:80", 1)
        assert "0 conflict(s)" in report

    def test_both_sides_touched_keeps_the_higher_version(self):
        east, west = split()
        east.write("billing/b1", "10.0.0.8:80", version=9)
        west.write("billing/b1", "10.0.0.9:80", version=7)
        merged, report = merge_partitions(east, west)
        assert merged["billing/b1"] == ("10.0.0.8:80", 9)
        assert (
            "east wins with 10.0.0.8:80@9 (west held "
            "10.0.0.9:80@7)"
        ) in report

    def test_the_loser_is_recorded_for_the_review(self):
        east, west = split()
        east.write("billing/b1", "a:1", version=9)
        west.write("billing/b1", "b:2", version=7)
        _, report = merge_partitions(east, west)
        assert "an answer for dashboards" in report

    def test_the_merge_cannot_resurrect_the_buried(self):
        east, west = split()
        east.delete("billing/b1", version=9)
        west.write("billing/b1", "10.0.0.9:80", version=7)
        merged, report = merge_partitions(east, west)
        assert "billing/b1" not in merged
        assert "cannot resurrect what one side buried" in report

    def test_a_newer_life_outruns_an_old_grave(self):
        east, west = split()
        east.delete("billing/b1", version=6)
        west.write("billing/b1", "10.0.0.9:80", version=8)
        merged, _ = merge_partitions(east, west)
        assert merged["billing/b1"] == ("10.0.0.9:80", 8)


class TestSideDiscipline:
    def test_versions_advance_or_are_refused(self):
        east, _ = split()
        with pytest.raises(Invalid):
            east.write("billing/b1", "x", version=5)

    def test_deleting_the_absent_is_refused(self):
        east, _ = split()
        with pytest.raises(Invalid):
            east.delete("ghost", version=1)
