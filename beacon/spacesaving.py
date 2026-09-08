"""Space-Saving: find the heavy hitters in a stream with a fixed handful of counters.

Finding which names are queried most in a torrent of queries would
take a counter per name, but the heavy hitters, the few names that
dominate, can be found with only a fixed number of counters by the
Space-Saving algorithm. It keeps k counters. An item already tracked
simply increments its counter. A new item, when there is room, gets
its own counter at one. A new item arriving when all counters are
full evicts the current minimum, and here is the clever part: the
newcomer inherits the evicted counter's value plus one, rather than
starting at one, which means a tracked count is an overestimate that
absorbs the traffic of everything that passed through that slot. The
guarantee this buys is that a truly heavy hitter can never be
evicted, because its real count exceeds the minimum it would be
compared against, so it is always among the tracked, and the error
on any count is bounded by the minimum counter, one-sided upward. A
light item may be reported with an inflated count it inherited, but
a heavy one is never missed. The module tracks the counters,
inherits on eviction, and returns the top items, so heavy-hitter
detection costs k counters and a bounded overcount.
"""

from __future__ import annotations

from beacon.errors import Invalid


class SpaceSaving:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a space-saving summary needs at least one counter")
        self.capacity = capacity
        self.counts: dict[str, int] = {}

    def offer(self, item: str) -> None:
        if item in self.counts:
            self.counts[item] += 1
            return
        if len(self.counts) < self.capacity:
            self.counts[item] = 1
            return
        victim = min(self.counts, key=lambda key: (self.counts[key], key))
        inherited = self.counts.pop(victim)
        self.counts[item] = inherited + 1

    def estimate(self, item: str) -> int:
        return self.counts.get(item, 0)

    def top(self, n: int) -> list[tuple[str, int]]:
        return sorted(
            self.counts.items(), key=lambda kv: (-kv[1], kv[0])
        )[:n]
