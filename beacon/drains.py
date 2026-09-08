"""Connection draining: deregistration is a promise kept in two steps.

Yanking an instance from discovery does not end its open
connections; it ends its future ones, and the difference is
where deploys break users. The drain makes the two-step
explicit: first the instance leaves discovery so no new
callers arrive, then existing connections are given a grace
window to finish, tracked to zero or to the deadline,
whichever comes first, and only then may the process be
killed. The deadline exists because a stuck connection would
otherwise hold the deploy hostage forever, and the cutoff is
logged with the count it severed, because a deploy that
regularly severs connections at the deadline is not draining,
it is amputating on a schedule, and the fix belongs in the
application's request timeouts, not in a longer grace window
that merely slows the amputation down.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

GRACE_TICKS = 30


@dataclass
class DrainingInstance:
    instance_id: str
    open_connections: int
    drain_started: int | None = None
    severed: int = 0

    def begin_drain(self, now: int) -> str:
        if self.drain_started is not None:
            raise Invalid(
                f"{self.instance_id} is already draining; "
                "impatience does not speed a drain"
            )
        self.drain_started = now
        return (
            f"{self.instance_id} left discovery; no new "
            f"callers, {self.open_connections} existing "
            "connection(s) get their grace"
        )

    def connection_closed(self) -> str:
        if self.drain_started is None:
            raise Invalid(
                "connections close all day; only draining "
                "ones are counted down"
            )
        if self.open_connections == 0:
            raise Invalid("nothing left to close")
        self.open_connections -= 1
        return (
            f"{self.instance_id}: "
            f"{self.open_connections} remaining"
        )

    def may_kill(self, now: int) -> tuple[bool, str]:
        if self.drain_started is None:
            return False, (
                f"{self.instance_id} is not draining; killing "
                "it now is the outage, not the deploy"
            )
        if self.open_connections == 0:
            return True, (
                f"{self.instance_id} drained clean; every "
                "connection finished its own way"
            )
        elapsed = now - self.drain_started
        if elapsed >= GRACE_TICKS:
            self.severed = self.open_connections
            self.open_connections = 0
            return True, (
                f"{self.instance_id}: deadline severed "
                f"{self.severed} connection(s) after "
                f"{elapsed} tick(s); logged, because a stuck "
                "connection must not hold the deploy hostage"
            )
        return False, (
            f"{self.instance_id}: {self.open_connections} "
            f"connection(s) still open, "
            f"{GRACE_TICKS - elapsed} tick(s) of grace left"
        )


def fleet_drain_report(
    instances: list[DrainingInstance],
) -> str:
    if not instances:
        raise Invalid("no instances drained")
    clean = sum(
        1
        for held in instances
        if held.severed == 0 and held.open_connections == 0
    )
    severed_total = sum(held.severed for held in instances)
    line = (
        f"{len(instances)} drain(s): {clean} clean, "
        f"{severed_total} connection(s) severed at deadlines"
    )
    if severed_total > len(instances):
        line += (
            "; this deploy is not draining, it is amputating "
            "on a schedule, and the fix belongs in request "
            "timeouts, not a longer grace window"
        )
    return line
