"""The secondary: fresh, aging, or expired, and honest about which.

A secondary's copy has a lifecycle written into the SOA it
copied: refresh says how often to ask whether anything changed,
retry says how soon to ask again after a failed ask, and expire
is the hard deadline past which the copy may no longer be
served at all. The state machine's virtue is the third state:
between a failed refresh and expiry the secondary keeps
answering from its aging copy, because stale answers from a
recently healthy zone beat no answers during a primary outage,
but past expire it stops cold and refuses queries outright,
since a copy that has outlived its warranty is not stale, it
is fiction with a domain name. The clock accounting is where
implementations drift: the expire countdown runs from the last
successful refresh, not from the last attempt, and this module
keeps those two timestamps apart because conflating them lets
a secondary that has failed every refresh for a week believe
it is one retry from healthy.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Expired, Invalid
from beacon.serialmath import newer
from beacon.transfers import TransferPrimary


@dataclass
class Secondary:
    name: str
    refresh: int
    retry: int
    expire: int
    serial: int = 0
    last_success: int = 0
    last_attempt: int = 0
    holds_copy: bool = False
    refreshes: int = 0
    stale_served: int = 0

    def __post_init__(self) -> None:
        if not self.retry < self.refresh < self.expire:
            raise Invalid(
                "the SOA wants retry < refresh < expire, or "
                "the state machine chases its own tail"
            )

    def due(self, now: int) -> bool:
        if not self.holds_copy:
            return True
        anchor = max(self.last_success, self.last_attempt)
        interval = (
            self.refresh
            if self.last_attempt <= self.last_success
            else self.retry
        )
        return now - anchor >= interval

    def attempt_refresh(
        self, primary: TransferPrimary, now: int, reachable: bool
    ) -> str:
        self.last_attempt = now
        if not reachable:
            return (
                f"{self.name}: primary unreachable; retrying "
                f"in {self.retry}, serving the aging copy "
                "meanwhile"
            )
        status, deltas = primary.incremental_transfer(
            self.serial
        )
        self.last_success = now
        self.refreshes += 1
        if status == "NOT-MODIFIED":
            return f"{self.name}: current at serial {self.serial}"
        self.serial = deltas[-1].to_serial
        self.holds_copy = True
        return (
            f"{self.name}: advanced to serial {self.serial} "
            f"via {len(deltas)} delta(s)"
        )

    def bootstrap(
        self, primary: TransferPrimary, now: int
    ) -> str:
        serial, records = primary.full_transfer()
        self.serial = serial
        self.holds_copy = True
        self.last_success = now
        self.last_attempt = now
        return (
            f"{self.name}: bootstrapped at serial {serial} "
            f"with {len(records)} record(s)"
        )

    def answerable(self, now: int) -> bool:
        if not self.holds_copy:
            return False
        return now - self.last_success < self.expire

    def serve(self, now: int) -> str:
        if not self.answerable(now):
            raise Expired(
                f"{self.name}: the copy outlived its warranty "
                f"({self.expire} past the last successful "
                "refresh); past expire it is not stale, it is "
                "fiction with a domain name"
            )
        if now - self.last_success >= self.refresh:
            self.stale_served += 1
            return (
                f"{self.name}: serving an aging copy at serial "
                f"{self.serial}; stale beats silent during a "
                "primary outage"
            )
        return f"{self.name}: serving fresh at serial {self.serial}"

    def freshness(self, primary_serial: int) -> str:
        if not self.holds_copy:
            return f"{self.name}: no copy yet"
        if self.serial == primary_serial:
            return f"{self.name}: current"
        behind = newer(primary_serial, self.serial)
        state = "behind" if behind else "impossibly ahead"
        return (
            f"{self.name}: {state} (has {self.serial}, "
            f"primary at {primary_serial})"
        )
