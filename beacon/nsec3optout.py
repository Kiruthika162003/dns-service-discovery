"""NSEC3 opt-out: a signed gap that covers unsigned delegations without signing them.

Authenticated denial proves a name absent by exhibiting a signed
record that spans the gap where the name would sort, but in a
huge delegation-centric zone like a top-level domain most names
are unsigned delegations to customers, and minting a signed NSEC3
record for every one of them is enormous cost spent on names that
carry no security anyway. Opt-out is the bargain that makes such
zones signable. An NSEC3 record with the opt-out flag set spans a
range and promises only that no signed name exists inside it,
saying deliberately nothing about insecure delegations that might.
The cost is exact and must be stated plainly: an attacker can
insert an unsigned delegation into an opt-out gap and its
existence cannot be proven absent, so opt-out trades away the
ability to deny an insecure delegation in exchange for not signing
millions of them. Whether a given denial is sound turns on one
thing, the security status of the name being denied, and the
module decides exactly that rather than pretending opt-out is free.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

KINDS = ("secure", "insecure-delegation")


@dataclass(frozen=True)
class OptOutSpan:
    opt_out: bool

    def can_prove_absent(self, kind: str) -> bool:
        if kind not in KINDS:
            raise Invalid(
                f"{kind!r} is not a name status this denial "
                f"reasons about; it knows {', '.join(KINDS)}"
            )
        if kind == "secure":
            return True
        return not self.opt_out

    def explain(self, kind: str) -> str:
        if self.can_prove_absent(kind):
            return (
                f"{kind}: absence is provable; the span's "
                "signature covers it"
            )
        return (
            f"{kind}: absence is NOT provable under opt-out; an "
            "unsigned delegation may hide in the gap, which is "
            "the security opt-out trades for the signing savings"
        )


def savings_report(
    total_names: int, secure_names: int, opt_out: bool
) -> str:
    if secure_names > total_names:
        raise Invalid(
            "there cannot be more secure names than names; the "
            "count is inconsistent"
        )
    if not opt_out:
        return (
            f"no opt-out: all {total_names} names get an NSEC3 "
            "record, and every absence is provable"
        )
    unsigned = total_names - secure_names
    return (
        f"opt-out: {secure_names} secure names signed, "
        f"{unsigned} insecure delegations left unsigned; the "
        "savings are those unsigned records and the cost is that "
        "their absence cannot be proven"
    )
