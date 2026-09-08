"""DNSSEC validation states: the AD bit is a promise only Secure is allowed to make.

A validating resolver does not answer with a bare yes or no; it
reaches one of four states, and conflating them is how DNSSEC
fails open. Secure means a chain of signatures links the answer
to a trusted anchor, and only then may the resolver set the AD
bit, which is its promise that the data was authenticated.
Insecure means the resolver proved, through a signed gap in the
parent, that the zone is deliberately unsigned, so the answer is
served without AD but is not an error. Bogus means signatures
should exist and do not verify, the dangerous state, and it is
returned as SERVFAIL rather than passed through, because a Bogus
answer served as data is exactly the forgery validation exists
to catch. Indeterminate means no trust anchor covers the name
and the resolver cannot judge, which is not the same as Insecure
and must not borrow its AD-clear pass as if the silence were
proof. The module refuses to set AD on anything but Secure and
refuses to hand Bogus to a client as an answer.
"""

from __future__ import annotations

from beacon.errors import Invalid

STATES = ("secure", "insecure", "bogus", "indeterminate")


def _require(state: str) -> None:
    if state not in STATES:
        raise Invalid(
            f"{state!r} is not a validation state; the resolver "
            f"knows only {', '.join(STATES)}"
        )


def ad_bit(state: str) -> bool:
    _require(state)
    return state == "secure"


def rcode_for(state: str) -> str:
    _require(state)
    if state == "bogus":
        return "SERVFAIL"
    return "NOERROR"


def is_served_as_data(state: str) -> bool:
    _require(state)
    return state != "bogus"


def describe(state: str) -> str:
    _require(state)
    reasons = {
        "secure": "chain to a trusted anchor verifies; AD set",
        "insecure": "a signed gap proves the zone is unsigned; "
        "served without AD, not an error",
        "bogus": "signatures should verify and do not; SERVFAIL, "
        "never passed through as data",
        "indeterminate": "no anchor covers this name; cannot "
        "judge, and silence is not proof of Insecure",
    }
    return f"{state}: {reasons[state]}"
