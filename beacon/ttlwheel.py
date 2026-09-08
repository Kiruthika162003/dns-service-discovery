"""A timing wheel: expire thousands of TTLs in O(1) per tick instead of a sorted heap's log.

A cache full of entries that each expire at their own time needs a
way to find what has expired without scanning everything, and the
obvious structure, a heap ordered by expiry, costs a logarithm per
insert and per expiry. A hashed timing wheel does better by giving
up exact ordering it does not need. It is a ring of buckets, one per
future tick within a revolution, and an entry expiring at some tick
is dropped into the bucket for that tick modulo the wheel size. The
clock advances one bucket per tick, and everything whose expiry has
actually come due in the bucket it lands on is expired at once,
which is constant work per tick regardless of how many timers exist.
The cost of the constant-time win is granularity, the wheel resolves
time only to the tick, and a fixed memory for the ring, and an entry
scheduled further ahead than one revolution must be remembered as
still having rounds to go before its bucket comes around to it as
due. The module schedules by absolute expiry tick, advances the
clock one tick at a time expiring exactly the entries now due, and
refuses a non-positive delay, which is an expiry in the past
masquerading as a schedule.
"""

from __future__ import annotations

from beacon.errors import Invalid


class TimingWheel:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise Invalid("a timing wheel needs at least one bucket")
        self.size = size
        self.current = 0
        self.buckets: list[list[tuple[str, int]]] = [
            [] for _ in range(size)
        ]

    def schedule(self, key: str, delay: int) -> None:
        if delay < 1:
            raise Invalid(
                f"a delay of {delay} is an expiry now or in the "
                "past, not a future schedule"
            )
        expiry = self.current + delay
        self.buckets[expiry % self.size].append((key, expiry))

    def advance(self) -> list[str]:
        self.current += 1
        slot = self.current % self.size
        due = [
            key
            for key, expiry in self.buckets[slot]
            if expiry == self.current
        ]
        self.buckets[slot] = [
            (key, expiry)
            for key, expiry in self.buckets[slot]
            if expiry != self.current
        ]
        return due
