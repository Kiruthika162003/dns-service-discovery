"""Selective Repeat: retransmit only the lost frames, at the price of a buffering receiver.

Selective Repeat is the reliable-delivery scheme that wastes no
bandwidth on frames that arrived. The receiver keeps a window and
buffers any frame that falls within it, acknowledging each frame
individually rather than only the in-order prefix, so out-of-order
arrivals are kept, not discarded. The sender, seeing which specific
frames were acknowledged, retransmits only the ones actually missing,
not the whole tail after a loss the way Go-Back-N would. On a path
that drops scattered frames this is a large saving, a few
retransmissions instead of a window's worth. The costs are the mirror
of Go-Back-N's simplicity: the receiver needs a reordering buffer and
per-frame acknowledgement, and there is a subtle correctness
requirement the module encodes, that the window must be at most half
the sequence-number space, because a window larger than that could
leave the receiver unable to tell a retransmitted old frame from a
brand-new one with the same wrapped sequence number, accepting the
wrong one. The module computes which frames a sender retransmits,
only the unacknowledged ones in the window, whether a receiver
buffers a frame, and whether a window size is safe against sequence
wraparound.
"""

from __future__ import annotations

from beacon.errors import Invalid


def frames_to_retransmit(
    window: list[int], acknowledged: set[int]
) -> list[int]:
    return [seq for seq in window if seq not in acknowledged]


def receiver_buffers(frame_seq: int, window_lo: int, window_size: int) -> bool:
    return window_lo <= frame_seq < window_lo + window_size


def window_safe(window_size: int, sequence_space: int) -> bool:
    if window_size < 1 or sequence_space < 2:
        raise Invalid(
            "a window needs at least one frame and a sequence space of "
            "at least two to wrap"
        )
    return window_size <= sequence_space // 2
