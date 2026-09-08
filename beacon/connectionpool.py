"""A connection pool: reuse warm connections, cap the total, and keep a few idle for the burst.

Opening a connection to a backend costs a handshake, so a busy
client pools connections and reuses them, but a pool is a balance
between two failures. Too small a pool serializes requests behind
the few connections it holds, adding queueing latency that has
nothing to do with the backend's own speed. Too large a pool
exhausts the backend, whose connection slots are finite, so a client
that opens without bound can take a shared backend down by
accepting more connections than it can serve. The pool therefore
caps the total it will open, refusing rather than exceeding it, and
it also keeps a floor of idle connections warm so a sudden burst is
served from the ready pool instead of paying a handshake per
request at exactly the moment latency matters most. A release
returns a connection to the idle set if the floor is not yet met and
otherwise closes it, so the pool holds warm connections for the
burst without hoarding idle ones forever. The module tracks the
active and idle counts, acquires by reusing an idle connection or
creating one under the cap, refuses when the cap is reached, and
releases back toward the idle floor.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class ConnectionPool:
    def __init__(self, max_total: int, min_idle: int = 0) -> None:
        if max_total < 1:
            raise Invalid("a pool must allow at least one connection")
        if min_idle > max_total:
            raise Invalid(
                "the idle floor cannot exceed the total cap; the "
                "pool cannot keep more warm than it may open"
            )
        self.max_total = max_total
        self.min_idle = min_idle
        self.active = 0
        self.idle = 0

    def acquire(self) -> str:
        if self.idle > 0:
            self.idle -= 1
            self.active += 1
            return "reused"
        if self.active + self.idle < self.max_total:
            self.active += 1
            return "created"
        raise Refused(
            "the pool is at its total cap; opening more would risk "
            "exhausting the backend's finite connection slots"
        )

    def release(self) -> str:
        if self.active == 0:
            raise Invalid(
                "no connection is checked out to release; a double "
                "release would drift the counts negative"
            )
        self.active -= 1
        if self.idle < self.min_idle:
            self.idle += 1
            return "returned-idle"
        return "closed"
