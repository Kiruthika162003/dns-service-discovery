"""Cache key canonicalization: fold the case DNS ignores so one name is one entry.

DNS names are case-insensitive, so www.Example.COM and
www.example.com are the same name, and a cache that keyed entries
on the raw bytes would store them as different records, fragmenting
one name into many entries and missing on a lookup that should have
hit. Canonicalizing the key fixes it: lowercase the name, root it
with a trailing dot so www.example.com and www.example.com. do not
split, and include the type and class, since the same name answers
differently for A and MX and those must not collide. This connects
to 0x20 encoding, which deliberately randomizes the case of the
query name on the wire for anti-spoofing entropy, and the two only
coexist because the case lives in the query while the cache key is
canonical: the resolver varies the case going out and folds it away
before caching, so the entropy defends the transaction without ever
fragmenting the cache. The module canonicalizes a name and builds a
cache key from name, type, and class, and refuses an empty name,
which is the root and is not a cacheable lookup on its own.
"""

from __future__ import annotations

from beacon.errors import Invalid


def canonical(name: str) -> str:
    if name == "":
        raise Invalid(
            "an empty name is the root, not a cacheable lookup on "
            "its own"
        )
    folded = name.lower()
    if not folded.endswith("."):
        folded += "."
    return folded


def cache_key(
    name: str, rrtype: str, rrclass: str = "IN"
) -> tuple[str, str, str]:
    return (canonical(name), rrtype.upper(), rrclass.upper())


def same_entry(query_a: tuple[str, str], query_b: tuple[str, str]) -> bool:
    name_a, type_a = query_a
    name_b, type_b = query_b
    return cache_key(name_a, type_a) == cache_key(name_b, type_b)
