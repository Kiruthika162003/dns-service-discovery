"""A decaying counter: weight recent activity over old, so a spike fades instead of lingering.

Asking how hot a key is lately is not answered by a plain count,
which remembers a burst from an hour ago as vividly as a burst from a
second ago, so a key that was popular once looks popular forever. A
time-decaying counter answers the lately by letting old contributions
fade. Each event adds weight, and the accumulated value decays
exponentially with elapsed time, halving over a chosen half-life, so
a recent event counts near its full weight while one many half-lives
back counts for almost nothing. Reading the counter applies the decay
up to the current moment, so a burst that stops is forgotten smoothly
rather than pinned in a total, and a sustained stream settles at a
level proportional to its rate. The half-life is the memory dial: a
short one reacts fast and forgets fast, a long one is steadier but
slower to notice change. Against a windowed counter this needs no
array of buckets, only a single value and the timestamp it was last
updated, which is why it scales to one counter per key across millions
of keys. The module adds weight with decay applied to the update
moment, reads the decayed value at a later moment, and refuses a
non-positive half-life that would decay to nothing or never.
"""

from __future__ import annotations

from beacon.errors import Invalid


class DecayingCounter:
    def __init__(self, half_life: float) -> None:
        if half_life <= 0:
            raise Invalid(
                "the half-life must be positive; zero decays instantly "
                "and there is no negative time to decay over"
            )
        self.half_life = half_life
        self.value = 0.0
        self.last = 0

    def _decayed(self, now: int) -> float:
        elapsed = now - self.last
        return self.value * 0.5 ** (elapsed / self.half_life)

    def add(self, now: int, amount: float = 1.0) -> None:
        if now < self.last:
            raise Invalid("time does not run backward for the counter")
        self.value = self._decayed(now) + amount
        self.last = now

    def get(self, now: int) -> float:
        if now < self.last:
            raise Invalid("time does not run backward for the counter")
        return self._decayed(now)
