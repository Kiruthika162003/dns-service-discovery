"""NAPTR: order is the law, preference is only advice, and a terminal flag ends the walk.

A NAPTR record set describes how to rewrite a name into the next
lookup, and it carries two numbers that are easy to confuse.
Order is binding: the client must consider records in ascending
order and may not skip a lower order because a higher one looks
better, since order encodes a dependency the zone owner declared.
Preference is only a hint for breaking ties within one order,
the owner's suggestion of which equal-order record to prefer,
and a client is free to ignore it, which is exactly why it is
preference and not a second order. The flags decide whether the
walk continues: a terminal flag, one of A, S, or U, says this
record yields a final result, an address, an SRV target, or a
URI, and the rewriting stops, while an empty flag means the
replacement is itself another NAPTR name and the walk goes on.
The module refuses to reorder across order values and reads the
terminal flag as the stopping condition it is.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

TERMINAL_FLAGS = ("a", "s", "u")


@dataclass(frozen=True)
class NaptrRecord:
    order: int
    preference: int
    flags: str
    service: str
    replacement: str

    def __post_init__(self) -> None:
        flag = self.flags.lower()
        if flag and flag not in TERMINAL_FLAGS:
            raise Invalid(
                f"{self.flags!r} is not a NAPTR flag this "
                "resolver walks; it knows the terminal A, S, U "
                "and the empty continue-flag"
            )

    def is_terminal(self) -> bool:
        return self.flags.lower() in TERMINAL_FLAGS


def ordered(records: list[NaptrRecord]) -> list[NaptrRecord]:
    if not records:
        raise Invalid("an empty NAPTR set rewrites nothing")
    return sorted(records, key=lambda r: (r.order, r.preference))


def first(records: list[NaptrRecord]) -> NaptrRecord:
    return ordered(records)[0]


def walk_stops_at(records: list[NaptrRecord]) -> NaptrRecord:
    for record in ordered(records):
        if record.is_terminal():
            return record
    raise Invalid(
        "no terminal flag in the set; the rewrite walk never "
        "reaches a final result and would loop through "
        "replacements forever"
    )
