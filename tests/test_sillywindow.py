from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.sillywindow import receiver_may_advertise, sender_may_send


class TestReceiver:
    def test_it_withholds_a_tiny_window_opening(self):
        # only 1 byte freed, mss 1460, buffer 8000 -> min(1460,4000)=1460
        assert not receiver_may_advertise(1, mss=1460, buffer_size=8000)

    def test_it_advertises_a_worthwhile_opening(self):
        assert receiver_may_advertise(2000, mss=1460, buffer_size=8000)

    def test_a_bad_mss_is_refused(self):
        with pytest.raises(Invalid):
            receiver_may_advertise(100, mss=0, buffer_size=8000)


class TestSender:
    def test_a_full_segment_is_sent(self):
        assert sender_may_send(data_ready=2000, usable_window=2000, mss=1460)

    def test_a_small_piece_waits_without_a_push(self):
        assert not sender_may_send(data_ready=10, usable_window=10, mss=1460)

    def test_a_push_flushes_the_last_small_piece(self):
        assert sender_may_send(
            data_ready=10, usable_window=10, mss=1460, push=True
        )

    def test_nothing_ready_does_not_send(self):
        assert not sender_may_send(data_ready=0, usable_window=5000, mss=1460)
