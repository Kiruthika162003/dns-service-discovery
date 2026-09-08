from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lamportclock import LamportClock, total_order


class TestTicking:
    def test_a_local_event_advances_the_clock(self):
        clock = LamportClock("a")
        assert clock.tick() == 1
        assert clock.tick() == 2

    def test_a_receive_jumps_past_the_message(self):
        clock = LamportClock("a")
        clock.tick()  # local time 1
        assert clock.receive(5) == 6

    def test_a_receive_from_the_past_still_advances(self):
        clock = LamportClock("a")
        clock.tick()
        clock.tick()  # time 2
        assert clock.receive(1) == 3


class TestCausality:
    def test_a_caused_event_has_a_greater_timestamp(self):
        sender = LamportClock("a")
        receiver = LamportClock("b")
        sent = sender.send()  # 1
        got = receiver.receive(sent)  # 2
        assert got > sent


class TestTotalOrder:
    def test_timestamps_order_first(self):
        assert total_order(1, "z", 2, "a") == -1

    def test_the_node_id_breaks_ties(self):
        assert total_order(3, "a", 3, "b") == -1
        assert total_order(3, "b", 3, "a") == 1

    def test_identical_stamps_are_equal(self):
        assert total_order(3, "a", 3, "a") == 0


class TestConstruction:
    def test_an_empty_node_id_is_refused(self):
        with pytest.raises(Invalid):
            LamportClock("")
