from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.iprange import CidrRange, overlap_report


class TestParsing:
    def test_the_bounds_are_computed_exactly(self):
        low, high = CidrRange("192.168.1.0/24").bounds()
        assert high - low == 255

    def test_host_bits_set_is_refused_not_normalized(self):
        with pytest.raises(Invalid) as caught:
            CidrRange("10.0.0.5/8").bounds()
        assert "would hide a typo for another range" in str(
            caught.value
        )

    def test_a_missing_prefix_is_refused(self):
        with pytest.raises(Invalid):
            CidrRange("10.0.0.0").bounds()

    def test_a_bad_prefix_length_is_refused(self):
        with pytest.raises(Invalid):
            CidrRange("10.0.0.0/33").bounds()


class TestContainment:
    def test_the_supernet_contains_the_subnet(self):
        assert CidrRange("10.0.0.0/8").contains(
            CidrRange("10.1.0.0/16")
        )

    def test_disjoint_ranges_do_not_contain(self):
        assert not CidrRange("10.0.0.0/8").contains(
            CidrRange("192.168.0.0/16")
        )

    def test_overlap_is_symmetric(self):
        a = CidrRange("10.0.0.0/8")
        b = CidrRange("10.128.0.0/9")
        assert a.overlaps(b)
        assert b.overlaps(a)


class TestTheReport:
    def test_containment_is_named_as_a_dead_rule(self):
        report = overlap_report(
            ["10.0.0.0/8", "10.1.0.0/16"]
        )
        assert "1 overlap(s)" in report
        assert "the narrower rule is dead unless it sorts first" in (
            report
        )

    def test_clean_rules_match_one_each(self):
        report = overlap_report(
            ["10.0.0.0/8", "192.168.0.0/16"]
        )
        assert report == "no overlaps; each address matches one rule"
