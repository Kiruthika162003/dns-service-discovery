"""Selective acknowledgement: retransmit only the holes, not everything past the first loss.

A cumulative acknowledgement names the highest byte received with no
gap before it, which is simple but blunt: if one segment in the
middle of a window is lost while the rest arrive, the cumulative ACK
cannot acknowledge any of the segments beyond the hole, so the sender
learns only that everything after the loss is unconfirmed and, in the
worst case, retransmits all of it, most of which the receiver already
has. Selective acknowledgement lets the receiver report the
contiguous ranges it did receive above the gap, so the sender sees
exactly which segments are missing and retransmits only those,
leaving the successfully delivered tail alone. On a path dropping a
few scattered segments this is the difference between resending a
handful and resending a whole window, a large saving in wasted
bandwidth and time. The cost is that the receiver must track and the
sender must parse non-contiguous ranges rather than a single number.
The module computes the cumulative acknowledgement point, the
received ranges a SACK would report, and the set of segments a sender
must retransmit with and without SACK, so the saving is a concrete
comparison rather than a claim.
"""

from __future__ import annotations

from beacon.errors import Invalid


def cumulative_ack(received: set[int]) -> int:
    point = 0
    while point in received:
        point += 1
    return point


def retransmit_without_sack(received: set[int], highest_sent: int) -> set[int]:
    if highest_sent < 0:
        raise Invalid("the highest sent sequence is never negative")
    start = cumulative_ack(received)
    return set(range(start, highest_sent + 1))


def retransmit_with_sack(received: set[int], highest_sent: int) -> set[int]:
    if highest_sent < 0:
        raise Invalid("the highest sent sequence is never negative")
    start = cumulative_ack(received)
    return {
        seq
        for seq in range(start, highest_sent + 1)
        if seq not in received
    }
