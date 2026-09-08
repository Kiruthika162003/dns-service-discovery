"""Name length limits: 63 octets a label, 255 a name, counted the way the wire counts.

DNS names have hard size limits that live in the wire format, not
in the text, and getting the accounting wrong is how a name that
looks fine in a zone file is rejected on the wire. Each label is
prefixed on the wire by a length octet, so a label may hold at most
sixty-three octets, the largest value the low six bits of that
prefix can express, and the whole name may be at most two hundred
fifty-five octets including every length prefix and the final zero
octet that terminates the root. The text form hides both costs: it
shows the dots but not the length octets they stand for, and it
shows no trailing marker for the root. So a name of many short
labels can bump the limit through the per-label octets alone, a
subtlety the module makes concrete by counting the wire length as
the sum of each label's length plus one for its prefix, plus one
for the root. It refuses a label over sixty-three and a name whose
wire length exceeds two hundred fifty-five, with the measured size
named, so the rejection points at the real cost rather than the
visible characters.
"""

from __future__ import annotations

from beacon.errors import Invalid

MAX_LABEL = 63
MAX_NAME = 255


def check_label(label: str) -> None:
    if len(label) == 0:
        raise Invalid(
            "an empty label is only the root, which is not written "
            "as an ordinary label"
        )
    if len(label) > MAX_LABEL:
        raise Invalid(
            f"the label is {len(label)} octets, over the "
            f"{MAX_LABEL} the length prefix's six bits can express"
        )


def wire_length(labels: list[str]) -> int:
    return sum(len(label) + 1 for label in labels) + 1


def check_name(labels: list[str]) -> int:
    for label in labels:
        check_label(label)
    length = wire_length(labels)
    if length > MAX_NAME:
        raise Invalid(
            f"the name is {length} octets on the wire, over the "
            f"{MAX_NAME} limit; the length prefixes and the root "
            "octet count even though the text hides them"
        )
    return length
