"""Two-phase locking: acquire every lock before releasing any, and schedules stay serializable.

Two-phase locking is the discipline that guarantees a set of
concurrent transactions produce a result equivalent to some serial
order. The rule is in the name and is deceptively strict: a
transaction has a growing phase during which it acquires locks and a
shrinking phase during which it releases them, and once it has
released a single lock it may never acquire another. That one
constraint, no lock acquired after any lock released, is what forbids
the interleavings that would violate serializability, because it
means every transaction reaches a point where it holds all the locks
it will ever hold at once. Lock compatibility governs who may hold
what together: two shared, read, locks coexist, but an exclusive,
write, lock is incompatible with any other, so writers exclude
everyone. The discipline has a well-known consequence the module
notes: two transactions can each hold a lock the other needs and
wait forever, a deadlock, which is why 2PL is paired with deadlock
detection or prevention, and strict 2PL holds every lock until commit
to avoid cascading aborts at the cost of concurrency. The module
enforces the phase rule, refusing an acquire after a release, and
decides lock compatibility.
"""

from __future__ import annotations

from beacon.errors import Invalid


def compatible(held_mode: str, requested_mode: str) -> bool:
    return held_mode == "shared" and requested_mode == "shared"


class TwoPhaseLock:
    def __init__(self) -> None:
        self.phase = "growing"
        self.held: dict[str, str] = {}

    def acquire(self, resource: str, mode: str) -> None:
        if mode not in ("shared", "exclusive"):
            raise Invalid(f"{mode!r} is not a lock mode")
        if self.phase == "shrinking":
            raise Invalid(
                "cannot acquire a lock after releasing one; the "
                "two-phase rule forbids it, and breaking it breaks "
                "serializability"
            )
        self.held[resource] = mode

    def release(self, resource: str) -> None:
        if resource not in self.held:
            raise Invalid(f"no lock on {resource} to release")
        del self.held[resource]
        self.phase = "shrinking"
