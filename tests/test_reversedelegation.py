from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.reversedelegation import (
    build_delegation,
    cname_target,
    needs_classless,
)

ZONE = "2.0.192.in-addr.arpa."


class TestNeedsClassless:
    def test_a_sub_24_prefix_needs_the_workaround(self):
        assert needs_classless(27)

    def test_a_24_or_larger_delegates_cleanly(self):
        assert not needs_classless(24)
        assert not needs_classless(16)

    def test_an_out_of_range_prefix_is_refused(self):
        with pytest.raises(Invalid):
            needs_classless(40)


class TestCname:
    def test_the_target_points_into_the_range_subzone(self):
        assert cname_target(5, "0-31", ZONE) == f"5.0-31.{ZONE}"

    def test_a_bad_octet_is_refused(self):
        with pytest.raises(Invalid):
            cname_target(300, "0-31", ZONE)


class TestBuild:
    def test_a_range_builds_a_cname_per_address(self):
        delegation = build_delegation(0, 4, "0-31", ZONE)
        assert delegation[f"0.{ZONE}"] == f"0.0-31.{ZONE}"
        assert len(delegation) == 4

    def test_a_range_past_255_is_refused(self):
        with pytest.raises(Invalid):
            build_delegation(250, 10, "0-31", ZONE)
