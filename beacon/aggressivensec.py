"""Aggressive NSEC: answer a whole range of NXDOMAINs from one cached signed denial.

A validating resolver that receives a signed NSEC record has been
handed more than a single denial. The NSEC record proves that
between one existing name and the next in canonical order nothing
exists, an entire gap, and RFC 8198 lets the resolver use that proof
aggressively: for any later query whose name sorts within that gap,
it can answer NXDOMAIN straight from the cached NSEC without going
upstream at all, because the signature already proves no such name
exists. The payoff is two-fold. It cuts upstream load, since one
cached denial covers a range rather than a point, and it blunts the
random-subdomain attack, where a flood of queries for
never-existent names under a domain would otherwise each hit the
authority, because once the resolver holds NSEC records tiling the
namespace it answers the flood from cache. The requirement is that
the zone be signed, since the whole mechanism rests on the NSEC
signature; an unsigned zone offers no proof to be aggressive with.
The module decides whether a cached NSEC gap covers a queried name,
handling the canonical ordering and the wraparound at the zone apex,
and whether an NXDOMAIN can therefore be served from cache.
"""

from __future__ import annotations

from beacon.errors import Invalid


def covers(owner: str, next_name: str, qname: str) -> bool:
    owner = owner.lower()
    next_name = next_name.lower()
    qname = qname.lower()
    if owner == next_name:
        return qname != owner
    if owner < next_name:
        return owner < qname < next_name
    return qname > owner or qname < next_name


def can_answer_from_cache(
    qname: str, nsec_gaps: list[tuple[str, str]]
) -> bool:
    if not nsec_gaps:
        raise Invalid(
            "no cached NSEC records; there is no signed proof to be "
            "aggressive with, so the query must go upstream"
        )
    return any(
        covers(owner, next_name, qname) for owner, next_name in nsec_gaps
    )
