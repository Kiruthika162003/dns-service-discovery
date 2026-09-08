"""Serve-stale: during the outage, yesterday's truth beats today's silence.

When every upstream is down, a resolver holding expired
answers faces the protocol's most human choice: refuse
honestly, or serve what it knows was true recently while
saying so. RFC 8767 chose the second, with fences this module
keeps: stale service activates only after live resolution has
actually failed, never as a shortcut around a refresh; every
stale answer is marked stale with its age, because a client
that cannot tell fresh from embalmed will happily build on
the dead; and the stale window is bounded, after which the
answer graduates from stale to gone, since a record expired
three days ago describes a world nobody remembers operating.
The ledger splits the outage story into the three numbers an
operator reads first: refusals avoided, staleness served in
age-ticks, and the moment the window closed, which together
say whether serve-stale carried the outage or merely
postponed the same hard failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Expired, Invalid, Missing

STALE_WINDOW = 900


@dataclass
class StaleEntry:
    value: str
    expired_at: int


@dataclass
class StaleServer:
    entries: dict[str, StaleEntry] = field(default_factory=dict)
    refusals_avoided: int = 0
    age_ticks_served: int = 0
    graduations: int = 0

    def retire(
        self, name: str, value: str, expired_at: int
    ) -> None:
        self.entries[name] = StaleEntry(
            value=value, expired_at=expired_at
        )

    def serve_stale(
        self, name: str, now: int, live_failed: bool
    ) -> str:
        if not live_failed:
            raise Invalid(
                "serve-stale is an outage measure, not a "
                "shortcut around a refresh; try live first"
            )
        held = self.entries.get(name)
        if held is None:
            raise Missing(
                f"{name} has nothing even stale; the outage "
                "meets an empty cupboard"
            )
        age = now - held.expired_at
        if age < 0:
            raise Invalid(
                f"{name} has not expired yet; a fresh answer "
                "does not need this door"
            )
        if age >= STALE_WINDOW:
            self.graduations += 1
            raise Expired(
                f"{name} expired {age} tick(s) ago, past the "
                f"{STALE_WINDOW} window; it graduated from "
                "stale to gone, describing a world nobody "
                "remembers operating"
            )
        self.refusals_avoided += 1
        self.age_ticks_served += age
        return (
            f"{name} = {held.value} [STALE, expired {age} "
            "tick(s) ago]: marked, because a client that "
            "cannot tell fresh from embalmed builds on the "
            "dead"
        )

    def outage_ledger(self) -> str:
        return (
            f"{self.refusals_avoided} refusal(s) avoided, "
            f"{self.age_ticks_served} age-tick(s) served, "
            f"{self.graduations} graduation(s) to gone; "
            "together these say whether serve-stale carried "
            "the outage or postponed the same failure"
        )
