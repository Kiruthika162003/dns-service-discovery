"""Graceful drain: stop taking new work, let the in-flight finish, then force what will not.

Shutting a server down while it is serving requests should not drop
those requests, so a graceful drain runs in phases. First the
server stops accepting new work and is removed from the load
balancer, so no fresh request lands on it. Then it waits for the
requests already in flight to complete on their own, which is the
polite part, the whole point of draining. But politeness cannot be
unbounded, because a single stuck request, one waiting on a
dependency that will never answer, would hold the drain open
forever and the deploy would hang. So the drain carries a deadline,
and once it passes the server stops waiting and forcibly terminates
whatever is still in flight, trading a few killed requests for a
shutdown that actually completes. The module reports the phase for a
given moment and in-flight count, refuses a new request once
draining has begun, and names the force phase as the deliberate
choice it is rather than letting a stuck request hold the shutdown
hostage.
"""

from __future__ import annotations

from beacon.errors import Refused


class Drain:
    def __init__(self, deadline: int) -> None:
        if deadline < 0:
            raise Refused("a drain deadline is never negative")
        self.deadline = deadline
        self.draining = False

    def begin(self) -> None:
        self.draining = True

    def accept(self) -> None:
        if self.draining:
            raise Refused(
                "the server is draining and accepts no new work; a "
                "fresh request belongs on a peer, not here"
            )

    def phase(self, now: int, inflight: int) -> str:
        if not self.draining:
            return "serving"
        if inflight == 0:
            return "drained"
        if now < self.deadline:
            return "draining"
        return "force"
