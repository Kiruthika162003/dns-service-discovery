from __future__ import annotations

import pytest

from beacon.congestionwindow import CongestionWindow
from beacon.errors import Invalid


class TestSlowStart:
    def test_the_window_doubles_below_the_threshold(self):
        cw = CongestionWindow(initial=1, ssthresh=16)
        assert cw.on_ack() == 2
        assert cw.on_ack() == 4
        assert cw.on_ack() == 8

    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            CongestionWindow(initial=0)


class TestAvoidance:
    def test_the_window_grows_additively_above_the_threshold(self):
        cw = CongestionWindow(initial=16, ssthresh=16)
        assert cw.on_ack() == 17
        assert cw.on_ack() == 18

    def test_it_leaves_slow_start_at_the_threshold(self):
        cw = CongestionWindow(initial=8, ssthresh=16)
        assert cw.in_slow_start()
        cw.on_ack()  # 16, now at threshold
        assert not cw.in_slow_start()


class TestLoss:
    def test_loss_halves_the_threshold_and_resets_the_window(self):
        cw = CongestionWindow(initial=32, ssthresh=16)
        cw.on_loss()
        assert cw.ssthresh == 16
        assert cw.cwnd == 1

    def test_the_retreat_is_multiplicative(self):
        cw = CongestionWindow(initial=64, ssthresh=64)
        cw.on_loss()
        assert cw.ssthresh == 32
