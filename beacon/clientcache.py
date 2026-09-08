"""The client's own cache: discovery survives the registry's bad hour.

A client that asks the registry before every call has coupled
its uptime to the registry's, which inverts the entire point
of keeping instance lists. The client cache holds the last
good answer per service with its fetch time, serves it fresh
within the horizon, and during a registry outage degrades in
declared steps rather than a cliff: fresh answers serve
normally, aging answers serve with a staleness mark, and past
the hard ceiling the client fails its calls rather than dial
addresses old enough to be strangers. The backoff is the
other half: a client hammering a down registry every tick
joins the outage instead of surviving it, so retry intervals
double to a cap and the ledger counts the queries not sent,
which is the number that distinguishes a polite client from
a thundering one when the registry finally staggers back up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Expired, Invalid, Missing

FRESH_HORIZON = 30
HARD_CEILING = 300
BACKOFF_START = 1
BACKOFF_CAP = 64


@dataclass
class CachedList:
    instances: tuple[str, ...]
    fetched_at: int


@dataclass
class ClientCache:
    lists: dict[str, CachedList] = field(default_factory=dict)
    backoff: int = BACKOFF_START
    next_retry_at: int = 0
    queries_not_sent: int = 0

    def store(
        self, service: str, instances: tuple[str, ...], now: int
    ) -> None:
        if not instances:
            raise Invalid(
                "an empty list is not worth remembering; "
                "cache answers, not absences"
            )
        self.lists[service] = CachedList(
            instances=instances, fetched_at=now
        )
        self.backoff = BACKOFF_START

    def serve(self, service: str, now: int) -> str:
        held = self.lists.get(service)
        if held is None:
            raise Missing(
                f"{service} was never fetched; there is no "
                "yesterday to fall back on"
            )
        age = now - held.fetched_at
        if age <= FRESH_HORIZON:
            return (
                f"{service}: {len(held.instances)} "
                f"instance(s), fresh"
            )
        if age < HARD_CEILING:
            return (
                f"{service}: {len(held.instances)} "
                f"instance(s) [STALE, {age} tick(s) old]; "
                "declared steps, not a cliff"
            )
        raise Expired(
            f"{service}: the list is {age} tick(s) old, past "
            f"the {HARD_CEILING} ceiling; these addresses are "
            "old enough to be strangers and the call fails "
            "honestly instead"
        )

    def may_query_registry(self, now: int) -> bool:
        if now >= self.next_retry_at:
            return True
        self.queries_not_sent += 1
        return False

    def registry_failed(self, now: int) -> str:
        self.next_retry_at = now + self.backoff
        verdict = (
            f"backing off {self.backoff} tick(s); a client "
            "hammering a down registry joins the outage "
            "instead of surviving it"
        )
        self.backoff = min(self.backoff * 2, BACKOFF_CAP)
        return verdict

    def politeness_ledger(self) -> str:
        return (
            f"{self.queries_not_sent} query(ies) not sent "
            "during backoff; the number that distinguishes a "
            "polite client from a thundering one when the "
            "registry staggers back up"
        )
