"""Ricart-Agrawala: fold the release into deferred replies and enter on unanimous consent.

Ricart-Agrawala refines Lamport's mutual exclusion to fewer messages
by making the reply itself carry the permission. A node wanting the
critical section timestamps a request and sends it to every other
node, and it enters only when it has received a reply from all of
them. The decision each receiver makes is where the algorithm lives.
A receiver replies immediately unless it either holds the critical
section now or wants it with priority, an earlier timestamp, or an
equal timestamp and a lower node id, in which case it defers the
reply, holding it back until it is done, and sends all its deferred
replies on release. So a node collecting a full set of replies knows
every peer has either no interest or a later request, which is
exactly the condition to enter safely, and release is not a separate
broadcast but the flushing of those deferred replies, which is the
message saving over Lamport's scheme. The trade that remains is the
same fundamental one: entry needs a reply from every node, so an
unreachable peer stalls the requester, since there is no quorum, only
unanimity. The module decides whether a receiver defers a reply from
its state and the two timestamps, and whether a requester with its
replies may enter.
"""

from __future__ import annotations

from beacon.errors import Invalid

STATES = ("idle", "wanted", "held")


def should_defer(
    my_state: str,
    my_timestamp: int,
    my_node: str,
    incoming_timestamp: int,
    incoming_node: str,
) -> bool:
    if my_state not in STATES:
        raise Invalid(f"{my_state!r} is not a known state")
    if my_state == "held":
        return True
    if my_state == "wanted":
        return (my_timestamp, my_node) < (incoming_timestamp, incoming_node)
    return False


def may_enter(replies_received: int, total_others: int) -> bool:
    if replies_received > total_others:
        raise Invalid(
            "more replies than peers; a node cannot reply more than "
            "once to a request"
        )
    return replies_received == total_others
