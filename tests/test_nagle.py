from __future__ import annotations

from beacon.nagle import may_send, stalls_on_delayed_ack


class TestMaySend:
    def test_nagle_holds_a_small_write_while_unacked(self):
        assert not may_send(
            payload_is_small=True, unacked_outstanding=True, nagle_on=True
        )

    def test_a_large_write_is_sent_regardless(self):
        assert may_send(
            payload_is_small=False, unacked_outstanding=True, nagle_on=True
        )

    def test_nothing_outstanding_lets_a_small_write_go(self):
        assert may_send(
            payload_is_small=True, unacked_outstanding=False, nagle_on=True
        )

    def test_nagle_off_always_sends(self):
        assert may_send(
            payload_is_small=True, unacked_outstanding=True, nagle_on=False
        )


class TestStall:
    def test_nagle_plus_delayed_ack_on_small_rpc_stalls(self):
        assert stalls_on_delayed_ack(
            nagle_on=True, delayed_ack_on=True, small_request_response=True
        )

    def test_disabling_nagle_avoids_the_stall(self):
        assert not stalls_on_delayed_ack(
            nagle_on=False, delayed_ack_on=True, small_request_response=True
        )
