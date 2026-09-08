"""Negative-cache TTL: how long a does-not-exist answer lives, from the SOA, capped by RFC 2308.

A positive answer carries its own TTL, but a negative answer, an
NXDOMAIN or a NODATA, is the absence of a record, so there is no
record TTL to cache it by, and the resolver needs some other value to
decide how long to remember that a name does not exist. RFC 2308
supplies it from the zone's SOA record, which accompanies a negative
answer, and it takes the smaller of two fields: the SOA's own TTL and
the SOA MINIMUM field, which was repurposed by RFC 2308 to mean the
negative-cache duration. Taking the minimum of the two matters,
because it stops a large MINIMUM from pinning a does-not-exist answer
longer than the zone's own cadence would justify, so a name that is
about to be added does not stay invisible for days after it starts
existing just because the negative answer was cached too long. Under-
caching negatives wastes upstream queries repeating a known no; over-
caching them delays the visibility of newly created names, and the
min-of-two rule balances toward not hiding new names. The module
computes the negative TTL as that minimum and refuses negative
inputs, since a lifetime below zero is not a duration a cache can
honor.
"""

from __future__ import annotations

from beacon.errors import Invalid


def negative_ttl(soa_ttl: int, soa_minimum: int) -> int:
    if soa_ttl < 0 or soa_minimum < 0:
        raise Invalid(
            "a TTL is never negative; a does-not-exist answer "
            "cannot be cached for less than no time"
        )
    return min(soa_ttl, soa_minimum)


def over_caches_new_names(soa_ttl: int, soa_minimum: int, refresh: int) -> bool:
    return negative_ttl(soa_ttl, soa_minimum) > refresh
