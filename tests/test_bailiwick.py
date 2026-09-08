from __future__ import annotations

import pytest

from beacon.bailiwick import BailiwickFilter
from beacon.errors import Invalid
from beacon.names import Name
from beacon.records import Record

COM = Name.parse("example.com")


def a_record(name: str, address: str) -> Record:
    return Record(
        name=Name.parse(name),
        rtype="A",
        value=address,
        ttl=300,
    )


class TestTheDistrict:
    def test_in_district_testimony_is_kept(self):
        chosen = BailiwickFilter()
        kept = chosen.filter_response(
            COM,
            [a_record("www.example.com", "192.0.2.1")],
            now=0,
        )
        assert len(kept) == 1
        assert chosen.accepted == 1

    def test_the_helpful_liar_is_discarded_unstored(self):
        chosen = BailiwickFilter()
        kept = chosen.filter_response(
            COM,
            [
                a_record("www.example.com", "192.0.2.1"),
                a_record("bank.net", "203.0.113.66"),
            ],
            now=5,
        )
        assert [r.name.canonical() for r in kept] == [
            "www.example.com."
        ]
        assert len(chosen.discard_log) == 1
        assert "wrong district" in chosen.discard_log[0]

    def test_a_sibling_zone_is_still_outside(self):
        chosen = BailiwickFilter()
        kept = chosen.filter_response(
            COM,
            [a_record("www.examp1e.com", "203.0.113.9")],
            now=0,
        )
        assert kept == []

    def test_an_empty_response_belongs_elsewhere(self):
        with pytest.raises(Invalid) as caught:
            BailiwickFilter().filter_response(COM, [], now=0)
        assert "handle it as a negative" in str(caught.value)


class TestTheRattling:
    def test_a_quiet_door_says_so(self):
        chosen = BailiwickFilter()
        chosen.filter_response(
            COM, [a_record("www.example.com", "192.0.2.1")], now=0
        )
        assert "the door is quiet" in chosen.rattling_report(0)

    def test_the_rattling_gets_timestamps(self):
        chosen = BailiwickFilter()
        for tick in (10, 11, 12):
            chosen.filter_response(
                COM,
                [a_record("bank.net", "203.0.113.66")],
                now=tick,
            )
        report = chosen.rattling_report(window_start=10)
        assert report.startswith("3 out-of-district record(s)")
        assert "[11] bank.net. A discarded" in report

    def test_old_rattling_falls_out_of_the_window(self):
        chosen = BailiwickFilter()
        chosen.filter_response(
            COM, [a_record("bank.net", "203.0.113.66")], now=1
        )
        assert "the door is quiet" in chosen.rattling_report(
            window_start=100
        )
