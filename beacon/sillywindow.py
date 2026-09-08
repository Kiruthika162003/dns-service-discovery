"""Silly window syndrome avoidance: refuse to trickle data in tiny segments or windows.

Silly window syndrome is a degenerate state where a TCP connection
moves data one small piece at a time, each piece carrying a full-size
header, so the link fills with overhead and almost no payload. It
arises from either end. A receiver whose buffer is nearly full might
advertise a one-byte window opening the instant it consumes a byte,
inviting the sender to send a one-byte segment, over and over. A
sender with a little data ready might dispatch it immediately in a
tiny segment rather than waiting to accumulate a useful amount.
Avoidance closes both doors. The receiver does not advertise a window
increase until it can offer a worthwhile amount, at least a full
segment or half its buffer, so small openings are hidden until they
add up. The sender does not transmit a small segment while data is in
flight, waiting until it has a full segment or the receiver's window
allows a full one, which is the same restraint Nagle's algorithm
imposes. The trade is a little added latency for escaping the tiny-
packet spiral. The module decides whether a receiver may advertise a
window and whether a sender may send, encoding both halves of the
avoidance.
"""

from __future__ import annotations

from beacon.errors import Invalid


def receiver_may_advertise(
    newly_available: int, mss: int, buffer_size: int
) -> bool:
    if mss < 1 or buffer_size < 1:
        raise Invalid("the MSS and buffer size must be positive")
    return newly_available >= min(mss, buffer_size // 2)


def sender_may_send(
    data_ready: int, usable_window: int, mss: int, push: bool = False
) -> bool:
    if mss < 1:
        raise Invalid("the MSS must be positive")
    sendable = min(data_ready, usable_window)
    if sendable <= 0:
        return False
    if sendable >= mss:
        return True
    return push and sendable == data_ready
