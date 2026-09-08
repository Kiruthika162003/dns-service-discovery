"""NOTIFY: the primary taps the secondaries so freshness stops waiting on luck.

Refresh polling bounds staleness by the refresh interval, which
means a zone published at second one is invisible until second
sixty on average, and NOTIFY closes that gap: the primary tells
its secondaries a new serial exists, and the told secondary
refreshes now instead of eventually. The protocol's hazard is
the storm: a primary that notifies every secondary on every
publish, and republishes five times in a burst, sends five
waves nobody needed, so the suppressor coalesces, one
outstanding notification per secondary, refreshed in place
when the serial climbs again, released when the secondary
acknowledges. The ledger measures what NOTIFY actually buys,
staleness with polling alone against staleness with the tap,
and counts suppressed duplicates separately, because a storm
that was absorbed is a real event that cost real bookkeeping
and pretending it never happened hides the burst that caused
it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class PendingTap:
    serial: int
    first_sent: int
    updates: int = 0


@dataclass
class Notifier:
    secondaries: tuple[str, ...]
    pending: dict[str, PendingTap] = field(default_factory=dict)
    taps_sent: int = 0
    duplicates_absorbed: int = 0
    acknowledged: int = 0

    def __post_init__(self) -> None:
        if not self.secondaries:
            raise Invalid(
                "a notifier with nobody to notify is a bell "
                "in an empty tower"
            )

    def publish(self, serial: int, now: int) -> list[str]:
        sent = []
        for secondary in self.secondaries:
            held = self.pending.get(secondary)
            if held is None:
                self.pending[secondary] = PendingTap(
                    serial=serial, first_sent=now
                )
                self.taps_sent += 1
                sent.append(
                    f"tap {secondary}: serial {serial}"
                )
            else:
                held.serial = serial
                held.updates += 1
                self.duplicates_absorbed += 1
                sent.append(
                    f"absorbed for {secondary}: the standing "
                    f"tap now carries {serial}"
                )
        return sent

    def acknowledge(self, secondary: str, serial: int) -> str:
        held = self.pending.get(secondary)
        if held is None:
            raise Invalid(
                f"{secondary} acknowledges a tap nobody sent"
            )
        if serial < held.serial:
            return (
                f"{secondary} acknowledged {serial} but the "
                f"tap has climbed to {held.serial}; it stands"
            )
        del self.pending[secondary]
        self.acknowledged += 1
        return f"{secondary} caught up at {serial}; tap released"

    def storm_report(self) -> str:
        return (
            f"{self.taps_sent} tap(s) sent, "
            f"{self.duplicates_absorbed} duplicate(s) absorbed, "
            f"{self.acknowledged} acknowledged; the absorbed "
            "column is a real event with real bookkeeping, "
            "kept visible because it names the burst"
        )


def staleness_bought(
    refresh_interval: int, publishes: int, tap_latency: int
) -> str:
    if refresh_interval <= tap_latency:
        raise Invalid(
            "a tap slower than the polling it replaces buys "
            "nothing"
        )
    polling_average = refresh_interval // 2
    saved = polling_average - tap_latency
    return (
        f"{publishes} publish(es): polling alone averages "
        f"{polling_average} tick(s) of staleness, the tap "
        f"averages {tap_latency}, saving {saved} per publish "
        f"({publishes * saved} total)"
    )
