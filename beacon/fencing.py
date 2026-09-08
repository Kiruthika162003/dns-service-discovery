"""Fencing tokens: the check at the resource that a lock alone cannot make.

A distributed lock is not enough to keep a resource safe from two
writers, and the reason is the pause. A client acquires the lock,
then stalls, a garbage-collection pause, a scheduler preemption, a
network partition, long enough that the lock times out and a second
client acquires it, and then the first client wakes up, unaware it
ever lost the lock, and writes. The lock service did everything
right and the resource is still corrupted, because the lock was
checked when the write was decided, not when it landed. Fencing
tokens close the gap by making the check happen at the resource. The
lock service hands each acquisition a monotonically increasing
token, the client presents it with every write, and the resource
remembers the highest token it has honored and rejects any write
carrying a lower one. The paused first client comes back holding an
old token, the resource has already seen a higher one from the
second client, and the stale write is fenced out. The module models
the resource's side, the memory of the highest token and the
refusal of anything below it, because that refusal, not the lock,
is what actually makes the write safe.
"""

from __future__ import annotations

from beacon.errors import Fenced, Invalid


class FencedResource:
    def __init__(self) -> None:
        self.highest_seen = 0

    def accept(self, token: int) -> str:
        if token <= 0:
            raise Invalid(
                "a fencing token is a positive monotonically "
                "increasing number; zero or below is not a token "
                "the lock service ever issues"
            )
        if token < self.highest_seen:
            raise Fenced(
                f"token {token} is below the highest honored "
                f"{self.highest_seen}; a newer holder exists and "
                "this write is a stale writer waking from a pause"
            )
        self.highest_seen = token
        return "accepted"

    def would_accept(self, token: int) -> bool:
        return token >= self.highest_seen
