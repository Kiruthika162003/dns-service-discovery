"""SIEVE eviction: one FIFO queue, a visited bit, and a lazy hand that beats LRU with less work.

SIEVE is a recent cache eviction algorithm that reaches hit rates
matching or beating LRU while doing markedly less bookkeeping. It
keeps a single queue in insertion order, oldest first, and a visited
bit per entry, with a hand that sweeps the queue. Access is cheap: it
only sets the entry's visited bit, with no move-to-front and no
reordering, which is where it saves work over LRU. Eviction advances
the hand from the old end toward the new: at each entry it either
clears a set visited bit and moves on, giving that entry a reprieve
for having been used since the last sweep, or, on finding an entry
whose bit is already clear, evicts it. New items are appended at the
new end and the hand does not jump to them, so a one-time item that
is inserted and never revisited is reached by the hand and evicted
quickly, which is where SIEVE's scan resistance comes from: unvisited
newcomers are the first to go while revisited entries keep earning
reprieves. The cost is maturity, it is newer and less proven than
LRU, but its simplicity, one bit and a hand rather than a constantly
reordered list, is real. The module appends on insert, marks visited
on access, and evicts by advancing the hand past reprieved entries to
the first unvisited one.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Sieve:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a cache of zero capacity holds nothing")
        self.capacity = capacity
        self.order: list[str] = []
        self.visited: dict[str, bool] = {}
        self.hand = 0
        self.last_evicted: str | None = None

    def access(self, key: str) -> None:
        if key in self.visited:
            self.visited[key] = True
            return
        if len(self.order) >= self.capacity:
            self._evict()
        self.order.append(key)
        self.visited[key] = False

    def _evict(self) -> None:
        while True:
            if self.hand >= len(self.order):
                self.hand = 0
            candidate = self.order[self.hand]
            if self.visited[candidate]:
                self.visited[candidate] = False
                self.hand += 1
                continue
            self.order.pop(self.hand)
            del self.visited[candidate]
            self.last_evicted = candidate
            if self.hand >= len(self.order):
                self.hand = 0
            return

    def resident(self) -> set[str]:
        return set(self.order)
