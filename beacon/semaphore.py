"""A leased distributed semaphore: permits a crashed holder cannot keep forever.

Limiting how many workers may do something at once, hold a
connection to a fragile backend, run a heavy migration, needs a
semaphore, and a distributed one has a failure a local one does not:
a holder can crash while holding a permit, and if the permit is
simply a count that is decremented on acquire and incremented on
release, a crash that skips the release leaks the permit forever and
the pool slowly drains to zero. Leasing fixes it. A permit is
granted with an expiry, and the holder must renew it before it
lapses to keep it, so a crashed holder's permit expires on its own
and returns to the pool without anyone having to notice the crash.
The cost is the mirror of fencing: a holder that is merely slow, not
crashed, can have its lease lapse and its permit reclaimed while it
still believes it holds one, so lease-protected work must tolerate
that its permit may have been given away, exactly the stale-holder
problem a fencing token guards against. The module expires lapsed
leases on each operation, grants a permit while the pool has room,
renews and releases, and refuses to over-issue past the permit
count.
"""

from __future__ import annotations

from beacon.errors import Refused


class Semaphore:
    def __init__(self, permits: int) -> None:
        if permits < 1:
            raise Refused("a semaphore of zero permits admits nobody")
        self.permits = permits
        self.held: dict[str, int] = {}

    def _expire(self, now: int) -> None:
        lapsed = [h for h, expiry in self.held.items() if expiry <= now]
        for holder in lapsed:
            del self.held[holder]

    def acquire(self, holder: str, now: int, lease: int) -> None:
        self._expire(now)
        if holder in self.held:
            self.held[holder] = now + lease
            return
        if len(self.held) >= self.permits:
            raise Refused(
                "all permits are held; a crashed holder's permit "
                "will return when its lease lapses, but none is free "
                "now"
            )
        self.held[holder] = now + lease

    def renew(self, holder: str, now: int, lease: int) -> None:
        self._expire(now)
        if holder not in self.held:
            raise Refused(
                f"{holder} holds no permit to renew; its lease may "
                "have lapsed and been reclaimed while it was slow"
            )
        self.held[holder] = now + lease

    def release(self, holder: str) -> None:
        self.held.pop(holder, None)

    def available(self, now: int) -> int:
        self._expire(now)
        return self.permits - len(self.held)
