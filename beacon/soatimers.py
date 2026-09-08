"""SOA timers: a secondary keeps serving a zone it cannot refresh, until it is too old to trust.

A secondary name server does not hold the master copy of a zone; it
refreshes it from a primary on a schedule the zone's SOA record
dictates, and that record carries three timers that govern what
happens when the primary cannot be reached. Refresh is how often the
secondary checks whether the serial has advanced. Retry is the
shorter interval it drops to when a refresh fails, so it probes more
eagerly while the primary is down. Expire is the outer bound, the
longest the secondary may go without a successful refresh before it
must stop serving the zone entirely, because data that has not been
confirmed for that long is too stale to answer with. The design
choice the timers encode is that stale-but-recent beats an outage:
while the primary is briefly unreachable the secondary keeps serving
the last good copy rather than failing queries, and only when the
staleness crosses the expire horizon does it give up and return
failures instead of answers that can no longer be trusted. The
module tracks whether the secondary is still within its expire
window and refuses a configuration whose expire does not exceed its
refresh, since a zone that expires before it would even refresh can
never serve at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class SoaTimers:
    refresh: int
    retry: int
    expire: int

    def __post_init__(self) -> None:
        if self.expire <= self.refresh:
            raise Invalid(
                "expire must exceed refresh; a zone that expires "
                "before its next refresh can never serve at all"
            )
        if self.retry > self.refresh:
            raise Invalid(
                "retry should not exceed refresh; the failure "
                "interval is meant to probe more eagerly, not less"
            )

    def serving(self, now: int, last_success: int) -> bool:
        return now - last_success < self.expire

    def expired(self, now: int, last_success: int) -> bool:
        return not self.serving(now, last_success)

    def next_check(self, refresh_failing: bool) -> int:
        return self.retry if refresh_failing else self.refresh
