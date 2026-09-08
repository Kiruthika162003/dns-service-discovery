"""Go-Back-N: a simple receiver, paid for by retransmitting the whole window after one loss.

Go-Back-N is the reliable-delivery scheme that keeps the receiver as
simple as possible. The sender may have up to a window of unacked
frames outstanding, but the receiver accepts frames only in order:
it holds an expected sequence number, delivers a frame if it matches,
and discards any frame that arrives out of order, buffering nothing.
That simplicity has a cost on loss. When a frame is lost, every frame
the sender sent after it arrives at the receiver out of order and is
discarded, so once the loss is detected the sender must go back and
retransmit the lost frame and everything after it, even the frames
that reached the receiver intact, because the receiver threw them
away. So Go-Back-N wastes bandwidth in proportion to the window size
on every loss, trading that waste for a receiver that needs no
reordering buffer and no per-frame bookkeeping, the opposite balance
from Selective Repeat. The module computes which frames a sender
retransmits after a loss, all from the lost one onward, and whether a
receiver accepts a given frame, only the in-order one, so the
simple-receiver, costly-retransmit trade is explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def frames_to_retransmit(lost_seq: int, highest_sent: int) -> list[int]:
    if lost_seq < 0 or highest_sent < lost_seq:
        raise Invalid(
            "the lost sequence must be non-negative and no greater "
            "than the highest sent"
        )
    return list(range(lost_seq, highest_sent + 1))


def receiver_accepts(frame_seq: int, expected_seq: int) -> bool:
    return frame_seq == expected_seq
