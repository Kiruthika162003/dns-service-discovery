from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.names import Name
from beacon.zonefile import parse_zone

GOOD = """\
$ORIGIN example.com.
@ SOA 2026090801 3600 600 86400 300
; the web tier
www 300 A 192.0.2.10
blog 300 CNAME www
_api._tcp 60 SRV 10 5 8443 www
notes 60 TXT "hello there"
"""


class TestParsing:
    def test_a_clean_file_becomes_a_zone(self):
        zone = parse_zone(GOOD)
        status, rows = zone.lookup(
            Name.parse("www.example.com"), "A"
        )
        assert status == "ANSWER"
        assert rows[0].value == "192.0.2.10"

    def test_relative_names_complete_against_the_origin(self):
        zone = parse_zone(GOOD)
        _status, rows = zone.lookup(
            Name.parse("blog.example.com"), "A"
        )
        assert rows[0].value.canonical() == "www.example.com."

    def test_srv_lines_carry_all_four_numbers(self):
        zone = parse_zone(GOOD)
        _, rows = zone.lookup(
            Name.parse("_api._tcp.example.com"), "SRV"
        )
        assert rows[0].value.port == 8443
        assert rows[0].value.target.canonical() == (
            "www.example.com."
        )

    def test_comments_and_blanks_are_free(self):
        zone = parse_zone(GOOD)
        _, rows = zone.lookup(
            Name.parse("notes.example.com"), "TXT"
        )
        assert rows[0].value == b"hello there"


class TestRefusalsWithAddresses:
    def test_a_bad_octet_names_its_line(self):
        broken = GOOD + "bad 300 A 192.0.2.300\n"
        with pytest.raises(Invalid) as caught:
            parse_zone(broken)
        assert str(caught.value).startswith("line 8:")

    def test_records_before_the_origin_have_no_home(self):
        with pytest.raises(Invalid) as caught:
            parse_zone("www 300 A 192.0.2.1\n")
        assert "the origin comes first" in str(caught.value)

    def test_records_before_the_soa_are_premature(self):
        text = "$ORIGIN example.com.\nwww 300 A 192.0.2.1\n"
        with pytest.raises(Invalid) as caught:
            parse_zone(text)
        assert "before it is exercised" in str(caught.value)

    def test_two_origins_are_one_too_many(self):
        text = GOOD + "$ORIGIN other.com.\n"
        with pytest.raises(Invalid) as caught:
            parse_zone(text)
        assert "one zone, one origin" in str(caught.value)

    def test_two_soas_are_one_too_many(self):
        text = GOOD + "@ SOA 2 1 1 1 1\n"
        with pytest.raises(Invalid) as caught:
            parse_zone(text)
        assert "one zone, one authority" in str(caught.value)

    def test_a_wordy_ttl_is_named(self):
        text = GOOD + "www2 fast A 192.0.2.2\n"
        with pytest.raises(Invalid) as caught:
            parse_zone(text)
        assert "not a number of seconds" in str(caught.value)

    def test_a_file_without_authority_is_notes(self):
        with pytest.raises(Invalid) as caught:
            parse_zone("$ORIGIN example.com.\n")
        assert "notes, not a zone" in str(caught.value)
