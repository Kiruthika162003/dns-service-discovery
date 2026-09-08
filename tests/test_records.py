from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.names import Name
from beacon.records import Record, SrvTarget

WWW = Name.parse("www.example.com")


class TestIpv4:
    def test_a_proper_quad_is_accepted(self):
        record = Record(name=WWW, rtype="A", value="192.168.1.9", ttl=300)
        assert record.describe().endswith("A 192.168.1.9")

    def test_three_octets_are_not_an_address(self):
        with pytest.raises(Invalid) as caught:
            Record(name=WWW, rtype="A", value="10.0.1", ttl=60)
        assert "four octets or it is not an address" in str(
            caught.value
        )

    def test_an_octet_must_fit_in_a_byte(self):
        with pytest.raises(Invalid):
            Record(name=WWW, rtype="A", value="10.0.0.256", ttl=60)

    def test_leading_zeros_smell_of_octal(self):
        with pytest.raises(Invalid) as caught:
            Record(name=WWW, rtype="A", value="10.0.0.09", ttl=60)
        assert "half the world parses as octal" in str(
            caught.value
        )


class TestIpv6:
    def test_full_and_compressed_forms_pass(self):
        Record(
            name=WWW,
            rtype="AAAA",
            value="2001:0db8:0:0:0:0:0:1",
            ttl=60,
        )
        Record(name=WWW, rtype="AAAA", value="2001:db8::1", ttl=60)

    def test_two_compressions_are_ambiguous(self):
        with pytest.raises(Invalid) as caught:
            Record(
                name=WWW, rtype="AAAA", value="2001::db8::1", ttl=60
            )
        assert "one gap only" in str(caught.value)

    def test_seven_groups_without_a_gap_are_refused(self):
        with pytest.raises(Invalid):
            Record(
                name=WWW,
                rtype="AAAA",
                value="1:2:3:4:5:6:7",
                ttl=60,
            )


class TestTypedValues:
    def test_cname_targets_are_names_not_strings(self):
        with pytest.raises(Invalid) as caught:
            Record(
                name=WWW, rtype="CNAME", value="other.com", ttl=60
            )
        assert "parse first" in str(caught.value)

    def test_srv_fields_fit_their_bits(self):
        with pytest.raises(Invalid):
            SrvTarget(
                priority=70_000,
                weight=1,
                port=80,
                target=Name.parse("svc.example.com"),
            )
        with pytest.raises(Invalid):
            SrvTarget(
                priority=1,
                weight=1,
                port=0,
                target=Name.parse("svc.example.com"),
            )

    def test_txt_carries_uninterpreted_bytes(self):
        record = Record(
            name=WWW, rtype="TXT", value=b"v=spf1 -all", ttl=60
        )
        assert "v=spf1 -all" in record.describe()

    def test_unknown_types_name_what_the_beacon_speaks(self):
        with pytest.raises(Invalid) as caught:
            Record(name=WWW, rtype="MX", value="x", ttl=60)
        assert "it knows A, AAAA" in str(caught.value)


class TestTtl:
    def test_zero_means_do_not_cache_and_is_legal(self):
        Record(name=WWW, rtype="A", value="10.0.0.1", ttl=0)

    def test_a_week_is_the_ceiling(self):
        with pytest.raises(Invalid) as caught:
            Record(
                name=WWW,
                rtype="A",
                value="10.0.0.1",
                ttl=604_801,
            )
        assert "a week is the ceiling" in str(caught.value)
