"""A memtable: buffer writes in memory, flush a sorted immutable table past a size threshold.

Small writes scattered across a large on-disk structure are the
enemy of a storage engine, because each one is a random seek, and a
log-structured engine avoids them by buffering. Writes land first in
a memtable, an in-memory sorted map, where they are cheap, and only
when the memtable grows past a threshold is it flushed to disk, all
at once, as an immutable sorted table written sequentially. That
turns a stream of small random writes into occasional large
sequential ones, which disks and SSDs handle far better, and because
the flushed table is sorted and immutable it is cheap to read and
never rewritten in place. The honest gap the module names is
durability: the memtable lives in memory, so a crash loses whatever
has not been flushed, which is why a log-structured engine pairs the
memtable with a write-ahead log that records every write durably
before it enters the memtable, so the memtable is a performance
buffer and the log is the durability guarantee. The module buffers a
put, signals when the threshold is reached and a flush is due,
produces the sorted flush and clears, so the batching-for-sequential-
IO behavior and its reliance on a log are both explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


class MemTable:
    def __init__(self, threshold: int) -> None:
        if threshold < 1:
            raise Invalid(
                "a threshold of zero flushes on every write, which "
                "defeats the buffering the memtable exists for"
            )
        self.threshold = threshold
        self.data: dict[str, str] = {}

    def put(self, key: str, value: str) -> str:
        self.data[key] = value
        return "flush-due" if len(self.data) >= self.threshold else "buffered"

    def flush(self) -> list[tuple[str, str]]:
        if not self.data:
            raise Invalid("an empty memtable has nothing to flush")
        sorted_table = sorted(self.data.items())
        self.data = {}
        return sorted_table

    def size(self) -> int:
        return len(self.data)
