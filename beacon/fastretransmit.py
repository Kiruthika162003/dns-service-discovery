"""Fast retransmit: three duplicate ACKs are enough evidence of loss to resend without waiting.

When a segment is lost but the segments after it arrive, the receiver
keeps acknowledging the same highest-contiguous byte, because it
cannot advance past the hole, so the sender sees the same
acknowledgement number arrive again and again, a duplicate ACK per
later segment that got through. That pattern is strong evidence of a
single lost segment rather than a mere reordering, and fast
retransmit acts on it: after a threshold of duplicate acknowledgements,
conventionally three, the sender retransmits the apparently-lost
segment immediately instead of waiting out the retransmission
timeout, which can be far longer than the round trip. The threshold
of three, rather than one, is deliberate tolerance for reordering: a
network that delivers segments slightly out of order produces one or
two duplicate ACKs harmlessly, and reacting to those would cause
needless retransmissions, so waiting for three filters ordinary
reordering from real loss. The module recognizes a duplicate
acknowledgement, counts a run of them, and decides whether the run
has reached the threshold to fast-retransmit, so the early-loss
signal and its reordering tolerance are both explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def is_duplicate(previous_ack: int, new_ack: int) -> bool:
    return new_ack == previous_ack


def should_fast_retransmit(duplicate_count: int, threshold: int = 3) -> bool:
    if threshold < 1:
        raise Invalid(
            "a threshold below one would retransmit on no evidence "
            "at all"
        )
    return duplicate_count >= threshold


def tolerates_reordering(duplicate_count: int, threshold: int = 3) -> bool:
    return duplicate_count < threshold
