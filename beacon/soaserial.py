"""SOA serial formats: the date-based convention that traps you at 99 and on a switch.

A zone's serial number is the version a secondary compares to decide
whether to transfer, and it must only ever increase under the
serial-arithmetic rules. Two conventions are common and both have
sharp edges the module surfaces. The date-based format, the digits of
the date followed by a two-digit revision, so the third edit on the
eighth of September 2026 is 2026090803, is human-readable and tells
an operator at a glance when the zone last changed, but the two-digit
revision caps at ninety-nine edits in a single day, and the hundredth
edit has nowhere to go without rolling into the next day's date, which
is a real limit for a busy zone edited by automation. The second and
worse trap is switching conventions. A date-based serial like
2026090800 is an enormous number, over two billion, so a well-meant
switch to a unix-timestamp serial, which is a smaller number today,
would go backward, and every secondary would see the new serial as
older and refuse to transfer, silently freezing the zone. The module
builds a date-based serial, refuses a revision past ninety-nine, and
decides whether a proposed new serial actually counts as an increase,
so the switch trap is caught before it freezes a zone.
"""

from __future__ import annotations

from beacon.errors import Invalid

MODULUS = 2**32
HALF = 2**31


def date_serial(year: int, month: int, day: int, revision: int) -> int:
    if not 0 <= revision <= 99:
        raise Invalid(
            f"revision {revision} exceeds the two-digit field; the "
            "date-based format allows only 99 edits in a day"
        )
    return ((year * 100 + month) * 100 + day) * 100 + revision


def revisions_exhausted(revision: int) -> bool:
    return revision >= 99


def is_increase(old: int, new: int) -> bool:
    if not 0 <= old < MODULUS or not 0 <= new < MODULUS:
        raise Invalid("a serial is a 32-bit unsigned number")
    if old == new:
        return False
    return (new - old) % MODULUS < HALF


def switch_would_freeze(old_serial: int, new_serial: int) -> bool:
    return not is_increase(old_serial, new_serial)
