"""One question per query: the count field that looks flexible has exactly one legal value.

The DNS header carries a question count, QDCOUNT, a sixteen-bit
field that on its face invites a query to ask several questions at
once, and generations of newcomers have tried to use it that way.
It does not work, and the reason is not a bug but the absence of an
agreement: the protocol never defined how a response would signal
which answer belonged to which question, how the response codes
would combine when one question succeeds and another fails, or how
caching would key a multi-question answer, so no two
implementations ever agreed and the field settled at exactly one.
A well-formed query asks one question, a query with QDCOUNT zero
asks nothing and is only meaningful for a few special opcodes, and
a query with more than one is refused rather than half-answered,
because guessing at semantics the protocol never fixed is how a
resolver produces answers no client can safely interpret. The
module validates the count, names the single legal value, and
treats a plural question as the malformed input it is instead of
picking one question to answer and dropping the rest.
"""

from __future__ import annotations

from beacon.errors import Invalid


def validate_qdcount(qdcount: int, opcode: str = "QUERY") -> int:
    if qdcount < 0:
        raise Invalid("a question count cannot be negative")
    if qdcount == 0:
        if opcode in ("NOTIFY", "UPDATE"):
            return 0
        raise Invalid(
            "a QUERY with no question asks nothing; only a few "
            "special opcodes carry an empty question section"
        )
    if qdcount > 1:
        raise Invalid(
            f"QDCOUNT is {qdcount}; DNS carries exactly one "
            "question because the multi-question case was never "
            "given interoperable semantics, so it is refused, not "
            "half-answered"
        )
    return 1
