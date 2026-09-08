from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.gobackn import frames_to_retransmit, receiver_accepts


class TestRetransmit:
    def test_it_resends_from_the_lost_frame_onward(self):
        assert frames_to_retransmit(lost_seq=3, highest_sent=6) == [3, 4, 5, 6]

    def test_a_lone_loss_at_the_end_resends_just_it(self):
        assert frames_to_retransmit(6, 6) == [6]

    def test_an_invalid_range_is_refused(self):
        with pytest.raises(Invalid):
            frames_to_retransmit(5, 3)


class TestReceiver:
    def test_it_accepts_only_the_expected_frame(self):
        assert receiver_accepts(frame_seq=4, expected_seq=4)

    def test_it_discards_an_out_of_order_frame(self):
        assert not receiver_accepts(frame_seq=6, expected_seq=4)
