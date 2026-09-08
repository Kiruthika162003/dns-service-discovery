"""Leader leases: one coordinator, fenced by a token, never by faith.

A registry cluster elects one leader to serialize writes, and
the lease is how leadership is held: the leader renews before
expiry, and a leader that cannot renew loses the lease by
clock, not by courtesy. The failure this module makes
impossible is the two-leader write: a leader that pauses for
garbage collection past its expiry, wakes believing it still
leads, and writes. The fence is the fix that does not take
faith: every acquisition mints a strictly increasing token,
every write carries the writer's token, and the store refuses
any write bearing a token older than the newest it has seen.
The paused old leader's write bounces off the fence with the
token gap named, converting split brain from a corruption
event into a log line, which is the entire budget of the
design. Renewal is refused after expiry rather than quietly
granted, because a lease you can renew late is not a lease, it
is a suggestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Fenced, Invalid

LEASE_TICKS = 20


@dataclass
class LeaseStore:
    holder: str | None = None
    token: int = 0
    expires_at: int = 0
    highest_write_token: int = 0
    fenced: list[str] = field(default_factory=list)

    def acquire(self, candidate: str, now: int) -> str:
        if self.holder is not None and now < self.expires_at:
            raise Invalid(
                f"{self.holder} holds the lease until "
                f"{self.expires_at}; {candidate} waits its turn"
            )
        self.holder = candidate
        self.token += 1
        self.expires_at = now + LEASE_TICKS
        return (
            f"{candidate} leads with token {self.token} until "
            f"{self.expires_at}"
        )

    def renew(self, holder: str, now: int) -> str:
        if holder != self.holder:
            raise Invalid(
                f"{holder} cannot renew a lease it does not hold"
            )
        if now >= self.expires_at:
            raise Invalid(
                f"{holder} renewed at {now}, past expiry "
                f"{self.expires_at}; a lease you can renew "
                "late is a suggestion, not a lease"
            )
        self.expires_at = now + LEASE_TICKS
        return f"{holder} renewed until {self.expires_at}"

    def write(self, writer: str, token: int, what: str) -> str:
        if token < self.highest_write_token:
            gap = (
                f"{writer} wrote with token {token} against a "
                f"fence at {self.highest_write_token}: the "
                "paused old leader woke believing, and its "
                "write bounces off the fence"
            )
            self.fenced.append(gap)
            raise Fenced(gap)
        self.highest_write_token = token
        return f"{what} committed under token {token}"

    def split_brain_summary(self) -> str:
        if not self.fenced:
            return (
                "no fenced writes; either no split brain or "
                "nobody wrote during one"
            )
        return (
            f"{len(self.fenced)} split-brain write(s) converted "
            "from corruption into log lines, the entire budget "
            "of the design"
        )
