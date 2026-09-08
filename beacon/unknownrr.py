"""Unknown record types: cache and serve what you cannot parse, and never guess its insides.

New DNS record types are deployed at authoritative servers long
before every resolver in the world learns to parse them, so a
resolver that choked on a type it did not recognize would break
resolution for every new record humanity invents. RFC 3597 requires
the opposite: a resolver must treat an unknown type as opaque
bytes, caching and serving the record verbatim without understanding
its contents, so a new type flows through the old resolver
untouched and reaches the client that does understand it. There is
one rule that keeps opaque handling safe, and it is easy to get
wrong: a resolver must not apply name compression inside the RDATA
of a type it does not know, because compression pointers are only
valid where the parser knows a name lives, and rewriting bytes it
cannot interpret as if they held a name would corrupt the record.
So unknown RDATA is passed through byte for byte, presented in the
generic backslash-hash form with its length, and never compressed
or decompressed. The module classifies a type as known or opaque
and renders the opaque form, refusing to pretend it understands
what it does not.
"""

from __future__ import annotations

from beacon.errors import Invalid

KNOWN_TYPES = {
    1: "A",
    2: "NS",
    5: "CNAME",
    6: "SOA",
    15: "MX",
    16: "TXT",
    28: "AAAA",
    33: "SRV",
}


def is_known(rrtype: int) -> bool:
    return rrtype in KNOWN_TYPES


def render(rrtype: int, rdata: bytes) -> str:
    if rrtype < 0:
        raise Invalid("a record type number is never negative")
    if is_known(rrtype):
        return f"{KNOWN_TYPES[rrtype]} (parsed)"
    hexed = rdata.hex()
    return rf"TYPE{rrtype} \# {len(rdata)} {hexed}"


def may_compress_rdata(rrtype: int) -> bool:
    return is_known(rrtype)
