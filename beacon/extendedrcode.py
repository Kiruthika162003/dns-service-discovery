"""Extended response codes: twelve bits of error, but only if an OPT record carries them.

The original DNS header has four bits for the response code, room
for sixteen values, and DNS long ago outgrew them. EDNS extends
the code to twelve bits by stashing the upper eight in the OPT
record's TTL field, which is how errors like BADVERS and BADCOOKIE
above fifteen are expressed. The dependency is strict and easy to
forget: those upper bits live in the OPT record, so an extended
rcode can only be sent to a client that itself sent an OPT record,
because there is nowhere else to put the high bits. A server that
computed an extended rcode for a client that spoke plain DNS has no
way to send it and must degrade to a plain code the four bits can
hold, rather than truncate the extended code into a different
error it did not mean. The module composes the twelve-bit code
from its parts, splits a code back into low and high halves, and
refuses to express an above-fifteen code without an OPT record,
naming the fallback instead of silently sending a wrong four-bit
value.
"""

from __future__ import annotations

from beacon.errors import Invalid

EXTENDED_CODES = {
    16: "BADVERS",
    23: "BADCOOKIE",
}


def compose(low4: int, high8: int) -> int:
    if not 0 <= low4 <= 15:
        raise Invalid(f"the low half {low4} does not fit in 4 bits")
    if not 0 <= high8 <= 255:
        raise Invalid(f"the high half {high8} does not fit in 8 bits")
    return (high8 << 4) | low4


def split(rcode: int) -> tuple[int, int]:
    if rcode < 0:
        raise Invalid("a response code is never negative")
    return (rcode & 0xF, rcode >> 4)


def requires_opt(rcode: int) -> bool:
    return rcode > 15


def express(rcode: int, has_opt: bool) -> int:
    if requires_opt(rcode) and not has_opt:
        raise Invalid(
            f"rcode {rcode} needs an OPT record to carry its high "
            "bits, but the client sent none; degrade to a plain "
            "code rather than truncate it into a different error"
        )
    return rcode
