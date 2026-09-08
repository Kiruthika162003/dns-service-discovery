"""Lamport clocks: a total order that respects causality but cannot see concurrency.

A Lamport clock is the smallest mechanism that puts distributed
events in an order everyone agrees on. Each node keeps a counter,
bumps it on every local event, stamps outgoing messages with it,
and on receiving a message sets its counter to one past the larger
of its own and the message's, so if event a could have caused
event b then a's timestamp is strictly less than b's. Ordering the
timestamps, breaking ties by node id, yields a single total order
consistent with cause and effect, which is exactly enough to make
a replicated log or a mutual-exclusion protocol agree on who went
first. What the clock cannot do is the mirror image, and the
limitation must be stated because it is so easy to forget: a
smaller timestamp does not mean a caused b, only that a did not
happen after b, so two genuinely concurrent events get ordered by
the tie-break as if one preceded the other, and the clock offers
no way to tell that apart from real causation. Detecting
concurrency needs a version vector; a Lamport clock buys a cheap
total order at the price of that blindness, and the module makes
the trade explicit rather than implying the order means more than
it does.
"""

from __future__ import annotations

from beacon.errors import Invalid


class LamportClock:
    def __init__(self, node_id: str) -> None:
        if not node_id:
            raise Invalid("a clock needs a node id to break ties with")
        self.node_id = node_id
        self.time = 0

    def tick(self) -> int:
        self.time += 1
        return self.time

    def send(self) -> int:
        return self.tick()

    def receive(self, message_time: int) -> int:
        self.time = max(self.time, message_time) + 1
        return self.time


def total_order(
    a_time: int, a_node: str, b_time: int, b_node: str
) -> int:
    left = (a_time, a_node)
    right = (b_time, b_node)
    if left < right:
        return -1
    if left > right:
        return 1
    return 0
