from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.zonediff import diff_zones, review_page

OLD = {
    "www A": "192.0.2.10",
    "api A": "192.0.2.20",
    "blog CNAME": "www",
}
NEW = {
    "www A": "192.0.2.10",
    "blog CNAME": "cdn.external.net.",
    "shop A": "192.0.2.30",
}


class TestTheThreeCurrencies:
    def test_added_removed_changed_are_kept_apart(self):
        diff = diff_zones(OLD, NEW, 100, 101)
        assert diff.added == ["shop A"]
        assert diff.removed == ["api A"]
        assert diff.changed == ["blog CNAME"]

    def test_the_summary_reads_for_the_change_request(self):
        diff = diff_zones(OLD, NEW, 100, 101)
        assert diff.summary() == (
            "1 added, 1 removed, 1 changed; serial advanced "
            "100 -> 101"
        )


class TestTheSerialVerdicts:
    def test_the_silent_publish_is_refused(self):
        with pytest.raises(Invalid) as caught:
            diff_zones(OLD, NEW, 100, 100)
        assert "the classic silent publish" in str(caught.value)

    def test_the_backward_serial_is_refused(self):
        with pytest.raises(Invalid):
            diff_zones(OLD, NEW, 101, 100)

    def test_the_noop_publish_wakes_everyone_for_nothing(self):
        diff = diff_zones(OLD, OLD, 100, 101)
        assert "wakes every secondary for nothing" in (
            diff.serial_verdict
        )

    def test_stillness_agrees_with_itself(self):
        diff = diff_zones(OLD, OLD, 100, 100)
        assert diff.serial_verdict == (
            "nothing moved, serial agrees"
        )


class TestTheReview:
    def test_deletions_sort_above_additions(self):
        page = review_page(diff_zones(OLD, NEW, 100, 101))
        lines = page.splitlines()
        assert lines[1].startswith("  REMOVED api A")
        assert "outage filed in advance" in lines[1]
        assert lines[2].startswith("  CHANGED blog CNAME")
        assert "traffic that was working" in lines[2]
        assert lines[3].startswith("  added shop A")
