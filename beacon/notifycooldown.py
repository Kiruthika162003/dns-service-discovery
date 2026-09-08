"""NOTIFY debounce: collapse a burst of zone edits into one nudge to the secondaries.

When a zone changes, the primary sends a NOTIFY to its secondaries
so they refresh promptly instead of waiting out the refresh timer,
which is exactly what you want for a single edit. But a burst of
edits, a script rewriting many records in a second, would fire a
NOTIFY per change, and since each NOTIFY can prompt a secondary to
start checking and possibly transferring, the burst turns into a
storm of refreshes for a zone that is still being edited. Debouncing
tames it. After a NOTIFY is sent, further ones are suppressed for a
cooldown window, and the changes that arrive during the window are
simply covered by the next NOTIFY once the window clears, because a
NOTIFY carries no payload, it only says the zone moved, so one nudge
serves any number of edits behind it. The trade is a small bounded
delay, up to the cooldown, before secondaries learn of a change, in
exchange for collapsing a burst into a single notification. The
module decides whether a change sends a NOTIFY now or is coalesced
into the pending one, and refuses a non-positive cooldown, which
would debounce nothing.
"""

from __future__ import annotations

from beacon.errors import Invalid


class NotifyDebouncer:
    def __init__(self, cooldown: int) -> None:
        if cooldown <= 0:
            raise Invalid(
                "a cooldown of zero debounces nothing; every change "
                "would send its own NOTIFY, which is the storm this "
                "prevents"
            )
        self.cooldown = cooldown
        self.last_sent: int | None = None

    def on_change(self, now: int) -> str:
        if self.last_sent is None or now - self.last_sent >= self.cooldown:
            self.last_sent = now
            return "sent"
        return "coalesced"
