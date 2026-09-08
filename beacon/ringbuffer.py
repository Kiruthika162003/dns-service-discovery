"""A ring buffer: a fixed-size window that overwrites its oldest entry, on purpose.

A rolling record of recent events, the last N log lines, the last N
latencies, wants bounded memory no matter how long the stream runs,
and a ring buffer gives exactly that. It is a fixed-size array with a
head that advances circularly, so a push writes the next slot and,
once the buffer is full, overwrites the oldest entry rather than
growing. The overwrite is the feature, not a fault: the buffer holds
a sliding window of the most recent entries and deliberately forgets
everything older, which is what keeps its footprint constant while
the stream is unbounded. That makes it right for a recent-events
cache or a debug ring that must never grow without limit, and wrong
where older history matters, since it silently discards it. The push
returns whatever it evicted so a caller that does care can observe
what fell out of the window. The module writes to the circular head,
overwrites the oldest when full and returns the evicted entry,
reports the current contents from oldest to newest, and refuses a
capacity below one, which would be a window holding nothing.
"""

from __future__ import annotations

from beacon.errors import Invalid


class RingBuffer:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a ring buffer of zero capacity holds nothing")
        self.capacity = capacity
        self.buffer: list[str] = []
        self.head = 0

    def push(self, item: str) -> str | None:
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
            return None
        evicted = self.buffer[self.head]
        self.buffer[self.head] = item
        self.head = (self.head + 1) % self.capacity
        return evicted

    def contents(self) -> list[str]:
        if len(self.buffer) < self.capacity:
            return list(self.buffer)
        return self.buffer[self.head :] + self.buffer[: self.head]

    def is_full(self) -> bool:
        return len(self.buffer) == self.capacity
