"""Nagle's algorithm: coalesce small writes, but beware the stall when it meets delayed ACK.

Nagle's algorithm reduces the overhead of many tiny packets, each
carrying a large header for a small payload, by holding back a small
write while an earlier small segment is still unacknowledged, letting
the application's little writes coalesce into one larger segment. It
is a clear win for a chatty application that would otherwise flood
the network with runt packets. The trouble is its interaction with
delayed acknowledgement, a receiver optimization that holds back an
ACK briefly hoping to piggyback it on a reply. Put the two together
with a request-response pattern of small messages and they can
deadlock for the delay: the sender withholds its next small write
waiting for the ACK of the last one, while the receiver withholds
that ACK waiting for data to piggyback on, so both sit until the
delayed-ACK timer finally fires, adding a fixed and pointless latency
to every exchange. This is why latency-sensitive small-message
protocols set TCP_NODELAY to switch Nagle off. The module decides
whether a small write may be sent under Nagle given an outstanding
unacked segment, and detects the Nagle-plus-delayed-ACK stall
condition, so the coalescing benefit and its latency trap are both
explicit.
"""

from __future__ import annotations


def may_send(
    payload_is_small: bool, unacked_outstanding: bool, nagle_on: bool
) -> bool:
    if not nagle_on:
        return True
    return not (payload_is_small and unacked_outstanding)


def stalls_on_delayed_ack(
    nagle_on: bool, delayed_ack_on: bool, small_request_response: bool
) -> bool:
    return nagle_on and delayed_ack_on and small_request_response
