from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.pacing import inter_packet_interval, is_burst, paced_rate


class TestInterval:
    def test_the_interval_spreads_the_window_over_the_rtt(self):
        # 10 packets over a 100ms rtt -> one every 10ms
        assert inter_packet_interval(cwnd=10, rtt=100) == 10

    def test_a_bigger_window_paces_faster(self):
        assert inter_packet_interval(20, 100) < inter_packet_interval(10, 100)

    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            inter_packet_interval(0, 100)

    def test_a_zero_rtt_is_refused(self):
        with pytest.raises(Invalid):
            inter_packet_interval(10, 0)


class TestRate:
    def test_the_paced_rate_is_window_over_rtt(self):
        assert paced_rate(10, 100) == 0.1


class TestBurst:
    def test_sending_the_whole_window_at_once_is_a_burst(self):
        assert is_burst(sent_now=10, cwnd=10)

    def test_a_paced_trickle_is_not(self):
        assert not is_burst(sent_now=1, cwnd=10)
