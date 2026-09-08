"""Prefetch: the popular answer is refreshed before its clock runs out.

A cache entry's expiry lands on whichever unlucky client asks
next: that client eats the full upstream latency while everyone
who asked a second earlier rode the cache. Prefetching moves
the cost off the critical path: entries that have earned
popularity, asked often enough within their lifetime, are
refreshed shortly before expiry by the cache itself, so the
unlucky client stops existing for the names that matter. The
earning rule is the guard against waste: prefetching everything
doubles upstream load for a fleet of names nobody will ask
again, so only entries above the ask threshold get the
treatment, and the ledger prices both sides, expiry latencies
avoided on hot names against refreshes spent on names that
went cold between earning and expiry, the wasted column being
the tuning knob's honest input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

EARN_THRESHOLD = 3
PREFETCH_LEAD = 10


@dataclass
class WatchedEntry:
    name: str
    expires_at: int
    asks: int = 0
    prefetched: bool = False


@dataclass
class PrefetchPlanner:
    entries: dict[str, WatchedEntry] = field(default_factory=dict)
    cold_misses_avoided: int = 0
    wasted_refreshes: int = 0

    def admit(self, name: str, expires_at: int) -> None:
        self.entries[name] = WatchedEntry(
            name=name, expires_at=expires_at
        )

    def note_ask(self, name: str) -> None:
        held = self.entries.get(name)
        if held is None:
            raise Invalid(f"{name} is not admitted")
        held.asks += 1

    def due_for_prefetch(self, now: int) -> list[str]:
        due = []
        for held in self.entries.values():
            if held.prefetched:
                continue
            if held.asks < EARN_THRESHOLD:
                continue
            if 0 <= held.expires_at - now <= PREFETCH_LEAD:
                due.append(held.name)
        return sorted(due)

    def prefetch(self, name: str, new_expiry: int, now: int) -> str:
        held = self.entries.get(name)
        if held is None:
            raise Invalid(f"{name} is not admitted")
        if held.asks < EARN_THRESHOLD:
            raise Invalid(
                f"{name} has {held.asks} ask(s) against a "
                f"threshold of {EARN_THRESHOLD}; prefetching "
                "the unpopular doubles load for nobody"
            )
        held.prefetched = True
        held.expires_at = new_expiry
        return (
            f"{name} refreshed {held.expires_at - now} tick(s) "
            "of life ahead of the unlucky client"
        )

    def settle_expiry(self, name: str, asked_after: bool) -> str:
        held = self.entries.get(name)
        if held is None:
            raise Invalid(f"{name} is not admitted")
        if held.prefetched and asked_after:
            self.cold_misses_avoided += 1
            return (
                f"{name}: the unlucky client never existed"
            )
        if held.prefetched and not asked_after:
            self.wasted_refreshes += 1
            return (
                f"{name}: went cold between earning and "
                "expiry; the refresh was freight for nothing"
            )
        return f"{name}: expired unwatched, as unpopular names do"

    def ledger(self) -> str:
        return (
            f"{self.cold_misses_avoided} cold miss(es) "
            f"avoided, {self.wasted_refreshes} wasted "
            "refresh(es); the wasted column is the tuning "
            "knob's honest input"
        )
