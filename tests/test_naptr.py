from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.naptr import NaptrRecord, first, ordered, walk_stops_at


def records() -> list[NaptrRecord]:
    return [
        NaptrRecord(20, 10, "u", "E2U+sip", "!^.*$!sip:x@e.!"),
        NaptrRecord(10, 50, "", "", "next.example."),
        NaptrRecord(10, 20, "s", "SIP+D2U", "_sip._udp.e."),
    ]


class TestOrdering:
    def test_lowest_order_wins_regardless_of_preference(self):
        chosen = first(records())
        assert chosen.order == 10
        assert chosen.preference == 20

    def test_preference_only_breaks_ties_within_an_order(self):
        walk = ordered(records())
        assert [r.order for r in walk] == [10, 10, 20]
        assert walk[0].preference < walk[1].preference


class TestTerminalFlags:
    def test_the_walk_stops_at_the_first_terminal_record(self):
        stop = walk_stops_at(records())
        assert stop.is_terminal()
        assert stop.service == "SIP+D2U"

    def test_a_set_with_no_terminal_would_loop_and_is_refused(self):
        with pytest.raises(Invalid) as caught:
            walk_stops_at(
                [NaptrRecord(10, 10, "", "", "again.example.")]
            )
        assert "loop through replacements forever" in str(
            caught.value
        )


class TestRefusals:
    def test_an_unknown_flag_is_refused(self):
        with pytest.raises(Invalid):
            NaptrRecord(10, 10, "z", "svc", "repl.")

    def test_an_empty_set_is_refused(self):
        with pytest.raises(Invalid):
            ordered([])
