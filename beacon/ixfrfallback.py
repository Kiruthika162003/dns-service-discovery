"""IXFR with an AXFR fallback: ship only the changes, unless the changes are no longer known.

A secondary that is a few edits behind its primary should not
re-download an entire zone to catch up, so IXFR ships only the
difference: the primary keeps a journal of recent changes keyed by
serial number, and given the serial the secondary already has, it
sends just the records added and removed since. The mechanism has
a natural limit. The journal is finite and old entries are purged,
so a secondary that has been offline long enough that its serial
has fallen off the back of the journal cannot be brought forward
incrementally, because the changes it missed are simply gone. The
correct response is not to refuse, which would strand the
secondary, but to fall back to AXFR, a full transfer of the whole
zone, which always works because it needs no history. The module
decides between up-to-date, incremental, and full based on where
the secondary's serial sits relative to the journal, choosing the
cheap incremental path when the history covers the gap and the
complete path when it does not, so a secondary is never stranded
for having been away too long.
"""

from __future__ import annotations

from beacon.errors import Invalid
from beacon.serialmath import newer


def transfer_plan(
    client_serial: int,
    journal_serials: set[int],
    current_serial: int,
) -> str:
    if client_serial == current_serial:
        return "up-to-date"
    if newer(client_serial, current_serial):
        raise Invalid(
            f"the secondary's serial {client_serial} is ahead of "
            f"the primary's {current_serial}; a secondary cannot "
            "be newer than its source, so this is a misconfiguration"
        )
    if client_serial in journal_serials:
        return "ixfr"
    return "axfr"


def bytes_saved(
    ixfr_size: int, axfr_size: int, plan: str
) -> int:
    if plan == "ixfr":
        return axfr_size - ixfr_size
    return 0
