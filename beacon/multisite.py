"""Multi-site failover: the backup takes over fast and gives back slowly.

Two sites serve one name, primary and backup, and the policy
that routes between them has two speeds for two directions.
Failing over is fast: the primary misses its health floor and
traffic moves, because every tick of hesitation is served
errors. Failing back is slow on purpose: the primary must
hold its recovery for a damping window before traffic
returns, because the wounded primary that recovers for
thirty seconds at a time would otherwise drag every user
through the flap, and a failback that costs a second outage
teaches operators to pin traffic manually forever, which is
how failover systems end up decorative. The ledger counts
transitions and the time spent on the backup, and flags the
site pair whose history is mostly flapping, since a pair
that cannot hold a state has a health check problem wearing
a routing costume.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

FAILBACK_DAMPING = 20


@dataclass
class SitePair:
    primary: str
    backup: str
    serving: str = ""
    primary_healthy_since: int | None = None
    transitions: list[str] = field(default_factory=list)
    backup_ticks: int = 0
    last_check: int = 0

    def __post_init__(self) -> None:
        if self.primary == self.backup:
            raise Invalid(
                "one site twice is redundancy theater"
            )
        self.serving = self.primary

    def observe(
        self, primary_healthy: bool, now: int
    ) -> str:
        if self.serving == self.backup:
            self.backup_ticks += now - self.last_check
        self.last_check = now
        if self.serving == self.primary:
            if not primary_healthy:
                self.serving = self.backup
                self.primary_healthy_since = None
                self.transitions.append(f"[{now}] failover")
                return (
                    f"FAILOVER to {self.backup}: every tick "
                    "of hesitation is served errors"
                )
            return f"{self.primary} serving, healthy"
        if not primary_healthy:
            self.primary_healthy_since = None
            return (
                f"{self.backup} serving; the primary is "
                "still down"
            )
        if self.primary_healthy_since is None:
            self.primary_healthy_since = now
        held = now - self.primary_healthy_since
        if held >= FAILBACK_DAMPING:
            self.serving = self.primary
            self.primary_healthy_since = None
            self.transitions.append(f"[{now}] failback")
            return (
                f"FAILBACK to {self.primary} after holding "
                f"recovery {held} tick(s); a failback that "
                "costs a second outage teaches operators to "
                "pin traffic forever"
            )
        return (
            f"{self.backup} serving; the primary has held "
            f"recovery {held} of {FAILBACK_DAMPING} tick(s), "
            "and thirty-second recoveries do not count"
        )

    def routing_ledger(self) -> str:
        flaps = len(self.transitions)
        line = (
            f"{flaps} transition(s), {self.backup_ticks} "
            f"tick(s) served from {self.backup}"
        )
        if flaps >= 6:
            line += (
                "; a pair that cannot hold a state has a "
                "health check problem wearing a routing "
                "costume"
            )
        return line
