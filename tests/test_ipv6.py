from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ipv6 import canonical, compress, expand


class TestExpand:
    def test_it_fills_the_double_colon(self):
        assert expand("2001:db8::1") == [
            "2001",
            "0db8",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0001",
        ]

    def test_two_double_colons_are_refused(self):
        with pytest.raises(Invalid):
            expand("2001::db8::1")


class TestCompress:
    def test_it_collapses_the_longest_zero_run(self):
        groups = ["2001", "0db8", "0000", "0000", "0000", "0000", "0000", "0001"]
        assert compress(groups) == "2001:db8::1"

    def test_a_single_zero_group_is_not_collapsed(self):
        groups = ["2001", "0db8", "0000", "0001", "0002", "0003", "0004", "0005"]
        assert compress(groups) == "2001:db8:0:1:2:3:4:5"


class TestCanonical:
    def test_two_spellings_canonicalize_to_one(self):
        a = canonical("2001:0db8:0000:0000:0000:0000:0000:0001")
        b = canonical("2001:db8::1")
        assert a == b == "2001:db8::1"

    def test_the_loopback_compresses(self):
        assert canonical("0:0:0:0:0:0:0:1") == "::1"

    def test_the_unspecified_address(self):
        assert canonical("0:0:0:0:0:0:0:0") == "::"
