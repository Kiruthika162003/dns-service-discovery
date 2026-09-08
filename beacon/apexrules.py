"""The zone apex cannot be a CNAME, which is the whole reason ALIAS records exist.

A CNAME says this name is merely another name for that one and
therefore owns no records of its own, but the apex of a zone,
example. itself, must carry an SOA and NS records to exist as a
zone at all, and a name cannot be both an alias with no data and
an apex full of it. So a CNAME at the apex is forbidden, and the
refusal is not pedantry: a resolver that followed an apex CNAME
would lose the very SOA and NS that make the zone answerable and
delegated. The workaround the industry grew, ALIAS or ANAME, is
not a real DNS record but a server-side instruction to resolve
the target and serve its addresses as though they were the
apex's own A records, so the apex keeps its SOA and NS while
still tracking a moving target like a load balancer's changing
address. The module enforces the prohibition, enforces the wider
rule that a CNAME never coexists with other data at any name,
and names ALIAS flattening as the honest alternative rather than
pretending the apex CNAME could be permitted.
"""

from __future__ import annotations

from beacon.errors import Invalid

APEX_REQUIRED = frozenset({"SOA", "NS"})


def validate_apex(types: set[str]) -> str:
    if "CNAME" in types:
        raise Invalid(
            "a CNAME at the zone apex is forbidden; it would "
            "shadow the SOA and NS that make the zone answerable, "
            "which is why ALIAS flattening exists instead"
        )
    missing = APEX_REQUIRED - types
    if missing:
        raise Invalid(
            f"the apex is missing {', '.join(sorted(missing))}; a "
            "zone apex must carry both SOA and NS to exist"
        )
    return "apex valid"


def validate_name(types: set[str]) -> str:
    if "CNAME" in types and types != {"CNAME"}:
        others = ", ".join(sorted(types - {"CNAME"}))
        raise Invalid(
            f"a CNAME may not coexist with other data, but this "
            f"name also holds {others}; the alias owns no records "
            "of its own by definition"
        )
    return "name valid"


def flatten_alias(
    apex: str, target_addresses: list[str]
) -> list[tuple[str, str, str]]:
    if not target_addresses:
        raise Invalid(
            f"ALIAS flattening for {apex} resolved to no "
            "addresses; there is nothing to serve as the apex A "
            "set, and an empty apex is worse than a slow one"
        )
    return [(apex, "A", address) for address in target_addresses]
