"""Lamport's mutual exclusion: a request enters the critical section when it heads every queue.

Coordinating exclusive access without a central lock server is what
Lamport's distributed mutual exclusion algorithm does, using logical
timestamps to order requests fairly. A node wanting the critical
section timestamps a request and broadcasts it, and every node keeps
a queue of outstanding requests ordered by timestamp, breaking ties
by node id so the order is total and identical everywhere. A node may
enter the critical section only when two conditions hold: its own
request sits at the head of its queue, the earliest outstanding, and
it has received a message from every other node timestamped later
than its request, which proves no earlier request it has not yet seen
is in flight. Releasing broadcasts a release that removes the request
from every queue, letting the next in line proceed. The order is fair
and starvation-free because timestamps impose a FIFO discipline no
node can jump. The cost is participation: three messages per entry
per other node, and, more limiting, every node must be reachable and
responsive, so a single slow node stalls the whole system, the price
of total ordering with no coordinator. The module maintains the
timestamp-ordered queue, decides entry from the head and the acks,
and releases a held request.
"""

from __future__ import annotations

from beacon.errors import Invalid


class LamportMutex:
    def __init__(self) -> None:
        self.queue: list[tuple[int, str]] = []

    def request(self, timestamp: int, node: str) -> None:
        entry = (timestamp, node)
        if entry in self.queue:
            raise Invalid(
                f"{node} already has a request at {timestamp}; a "
                "node holds one outstanding request at a time"
            )
        self.queue.append(entry)
        self.queue.sort()

    def head(self) -> tuple[int, str] | None:
        return self.queue[0] if self.queue else None

    def may_enter(
        self, node: str, acks_received: int, total_nodes: int
    ) -> bool:
        top = self.head()
        if top is None or top[1] != node:
            return False
        return acks_received >= total_nodes - 1

    def release(self, node: str) -> None:
        for index, (_, owner) in enumerate(self.queue):
            if owner == node:
                self.queue.pop(index)
                return
        raise Invalid(f"{node} holds no request to release")
