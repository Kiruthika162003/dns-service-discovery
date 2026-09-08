"""Opcode dispatch: routing a message by its purpose, and retiring the one that was a mistake.

The DNS header's opcode says what kind of message this is, and a
server has to route each to a different machine: a QUERY looks up
records, a NOTIFY tells a secondary the zone changed, an UPDATE
mutates a zone under prerequisites, a STATUS is a diagnostic. One
opcode is a cautionary tale. IQUERY, the inverse query, asked a
server to work backward from an answer to a question, and it was
so underspecified and so useless that RFC 3425 formally obsoleted
it, so a modern server must not attempt it, it must answer NOTIMP,
because a server that improvised an inverse query would be
implementing a feature the standard deliberately removed. The
module maps each opcode to its handler name, refuses the retired
IQUERY with the not-implemented answer the standard requires, and
refuses an unknown opcode rather than guessing, since dispatching
an unrecognized purpose to any handler at all is how a malformed
message gets treated as a valid one.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused

OPCODES = {
    "QUERY": 0,
    "STATUS": 2,
    "NOTIFY": 4,
    "UPDATE": 5,
}

HANDLERS = {
    "QUERY": "lookup",
    "STATUS": "diagnostic",
    "NOTIFY": "zone-changed",
    "UPDATE": "mutate-zone",
}


def dispatch(opcode: str) -> str:
    if opcode == "IQUERY":
        raise Refused(
            "IQUERY (inverse query) was obsoleted by RFC 3425; a "
            "server answers NOTIMP rather than improvise a feature "
            "the standard deliberately removed"
        )
    if opcode not in HANDLERS:
        raise Invalid(
            f"{opcode!r} is not a known opcode; dispatching an "
            "unrecognized purpose to any handler treats a "
            "malformed message as a valid one"
        )
    return HANDLERS[opcode]


def code_of(opcode: str) -> int:
    if opcode not in OPCODES:
        raise Invalid(f"{opcode!r} has no assigned opcode number")
    return OPCODES[opcode]
