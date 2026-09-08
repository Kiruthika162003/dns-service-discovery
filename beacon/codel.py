"""CoDel: judge a queue by how long packets wait in it, not by how many are in it.

Queue management by length is fooled by the difference between a
good queue and a bad one. A good queue is a burst absorber, briefly
full and quickly drained, and its packets pass through fast; a bad
queue is a standing backlog that never empties, and its packets sit
for a long time. Both can be the same length at a glance, so a
length threshold either drops packets from a harmless burst or
tolerates a persistent backlog. CoDel measures the right thing, the
sojourn time each packet spends waiting, and it acts only when the
minimum sojourn over a whole interval stays above a small target,
which is the signature of a standing backlog no burst explains. A
brief spike where even the fastest packet is delayed does not
trigger it, because the minimum drops back below target as soon as
the queue drains, but a delay that never lets the minimum recover
does. The module tracks the interval during which the sojourn has
stayed above target and signals a drop once it has persisted,
distinguishing the bad queue that must be trimmed from the good one
that should be left alone.
"""

from __future__ import annotations

from beacon.errors import Invalid


class CoDel:
    def __init__(
        self, target_ms: float = 5.0, interval_ms: float = 100.0
    ) -> None:
        if target_ms <= 0 or interval_ms <= 0:
            raise Invalid(
                "the target and interval must be positive; a "
                "zero-length window judges nothing"
            )
        self.target_ms = target_ms
        self.interval_ms = interval_ms
        self.above_since: float | None = None

    def observe(self, sojourn_ms: float, now_ms: float) -> bool:
        if sojourn_ms <= self.target_ms:
            self.above_since = None
            return False
        if self.above_since is None:
            self.above_since = now_ms
            return False
        return now_ms - self.above_since >= self.interval_ms

    def is_standing(self) -> bool:
        return self.above_since is not None
