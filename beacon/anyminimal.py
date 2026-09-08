"""Minimal ANY: refusing to be the amplifier that answers a question nobody needs.

A query for ANY once returned every record at a name, which
made it a prized reflection weapon: a tiny spoofed request drew
a large signed response the attacker bounced off the resolver
at a victim, and the more the name held the better the leverage.
RFC 8482 lets an authority decline to enumerate. Instead of the
full set it returns a single synthetic HINFO record whose text
says ANY is not conveyed, so the response stays small and the
amplification factor collapses toward one. The module enforces
the rule that keeps this honest: minimal ANY is only for ANY. A
specific query for A or MX still receives its complete RRset,
because the amplification came from the wildcard question and
not from answering questions at all, and a server that also
minimized real queries would be breaking resolution to fix a
reflection problem those queries never had. The report measures
the factor so the operator sees the leverage the minimization
removed.
"""

from __future__ import annotations

from beacon.errors import NoData

SYNTHETIC_HINFO = 'HINFO "RFC8482" "ANY not conveyed"'


def answer(
    qtype: str,
    rrsets: dict[str, list[str]],
    minimal: bool = True,
) -> list[str]:
    if qtype == "ANY":
        if minimal:
            return [SYNTHETIC_HINFO]
        flattened = []
        for records in rrsets.values():
            flattened.extend(records)
        return flattened
    if qtype not in rrsets:
        raise NoData(
            f"the name exists but holds no {qtype}; a specific "
            "query is answered in full, never minimized"
        )
    return list(rrsets[qtype])


def full_size(rrsets: dict[str, list[str]]) -> int:
    return sum(len(records) for records in rrsets.values())


def amplification_factor(rrsets: dict[str, list[str]]) -> float:
    full = full_size(rrsets)
    minimal = len(answer("ANY", rrsets, minimal=True))
    return full / minimal if minimal else 0.0


def report(rrsets: dict[str, list[str]]) -> str:
    factor = amplification_factor(rrsets)
    return (
        f"full ANY returns {full_size(rrsets)} records, minimal "
        f"returns 1, an amplification of {factor:.0f}x the "
        "minimization removes; a specific query is untouched"
    )
