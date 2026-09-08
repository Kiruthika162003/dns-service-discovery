from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.selectiverepeat import (
    frames_to_retransmit,
    receiver_buffers,
    window_safe,
)


class TestRetransmit:
    def test_only_unacknowledged_frames_are_resent(self):
        window = [3, 4, 5, 6]
        acked = {3, 5}
        assert frames_to_retransmit(window, acked) == [4, 6]

    def test_a_fully_acked_window_resends_nothing(self):
        assert frames_to_retransmit([1, 2], {1, 2}) == []


class TestReceiver:
    def test_it_buffers_a_frame_in_the_window(self):
        assert receiver_buffers(frame_seq=5, window_lo=4, window_size=4)

    def test_it_rejects_a_frame_outside_the_window(self):
        assert not receiver_buffers(frame_seq=9, window_lo=4, window_size=4)


class TestWindowSafety:
    def test_a_window_at_half_the_space_is_safe(self):
        assert window_safe(window_size=4, sequence_space=8)

    def test_a_window_over_half_is_unsafe(self):
        assert not window_safe(window_size=5, sequence_space=8)

    def test_a_degenerate_space_is_refused(self):
        with pytest.raises(Invalid):
            window_safe(window_size=1, sequence_space=1)
