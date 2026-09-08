"""Chang-Roberts ring election: pass the maximum id around a ring until it returns to its owner.

In a ring of nodes where each can only talk to its successor, leader
election cannot use a global maximum because no node sees the whole
set, so Chang-Roberts elects by circulation. A node that starts an
election sends its own id to its successor. A node receiving an id
compares it to its own: if the incoming id is larger it forwards it
unchanged, if smaller it forwards its own id instead, and if the
incoming id equals its own it knows its id travelled the entire ring
without being beaten, so it is the maximum and declares itself the
leader. Only the largest id survives a full loop, because every
smaller id is replaced the moment it meets a larger node, so exactly
one node ever sees its own id return. The elegance is that no node
needs to know the ring's membership or size, only how to reach its
successor. The cost is messages: best case around the ring once, but
a pathological ordering makes many ids travel far before being
suppressed, up to a quadratic number of messages. The module computes
the id that survives the circulation, decides how a node forwards an
incoming id, and reports the leader, so the winner and the mechanism
are both explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def forward(incoming_id: int, own_id: int) -> int:
    return max(incoming_id, own_id)


def leader(ring: list[int]) -> int:
    if not ring:
        raise Invalid("an empty ring has no node to elect")
    if len(set(ring)) != len(ring):
        raise Invalid(
            "the ring has duplicate ids; election needs unique ids "
            "so exactly one id survives the loop"
        )
    surviving = ring[0]
    for node in ring[1:]:
        surviving = forward(surviving, node)
    return max(surviving, ring[0])
