"""Chandy-Lamport snapshot: record a consistent global cut without ever pausing the system.

Taking a snapshot of a distributed system, for a checkpoint or to
detect a stable property, is hard because there is no global clock to
freeze everything at one instant, and a naive snapshot that records
each process at a different moment can capture an inconsistent state,
one that records a message as received without recording it as sent,
an effect with no cause, a state that never actually existed. The
Chandy-Lamport algorithm records a consistent cut without stopping
the system, using marker messages: a process records its own state
and sends a marker on every outgoing channel, and a process receiving
a marker for the first time records its own state at once, then
treats messages arriving after on other channels as the recorded
in-flight state of those channels. The cut this produces is
consistent, meaning it never records a receive whose matching send it
did not also record, and the module checks exactly that property. A
cut assigns each process a point in its event sequence, and for every
message the cut is inconsistent if the receive falls before the cut
while the send falls after it, an effect recorded without its cause.
The module decides whether a proposed cut is consistent and points at
the offending message when it is not.
"""

from __future__ import annotations


def is_consistent_cut(
    messages: list[tuple[str, int, str, int]],
    cut: dict[str, int],
) -> bool:
    for sender, send_seq, receiver, recv_seq in messages:
        recorded_receive = recv_seq <= cut.get(receiver, 0)
        recorded_send = send_seq <= cut.get(sender, 0)
        if recorded_receive and not recorded_send:
            return False
    return True


def offending_message(
    messages: list[tuple[str, int, str, int]],
    cut: dict[str, int],
) -> tuple[str, int, str, int] | None:
    for message in messages:
        sender, send_seq, receiver, recv_seq = message
        if recv_seq <= cut.get(receiver, 0) and send_seq > cut.get(sender, 0):
            return message
    return None
