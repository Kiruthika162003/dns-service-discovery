"""CNAME flattening at the authority: follow the in-zone chain to the terminal data.

A CNAME is an alias, and a chain of them, alias to alias to a name
that finally holds addresses, means a resolver would ordinarily
make a query per hop. When the whole chain lives inside a single
authoritative zone, the server can do better: it already holds
every link, so it follows the chain itself and returns the terminal
data along with the CNAME records it traversed, saving the resolver
the round trips. The follow has the same hazard as any chain, a
CNAME that points back into the chain forms a loop, so the server
tracks the names it has visited and refuses to circle. It also
stops at the zone's edge: a CNAME pointing to a name in another
zone cannot be flattened here, because the server is not
authoritative for the target and must hand the resolver a referral
to chase rather than invent an answer it cannot vouch for. The
module walks the in-zone chain from a starting name, returns the
terminal name and its records with the traversed aliases, raises on
a loop, and stops at an out-of-zone target rather than following it.
"""

from __future__ import annotations

from beacon.errors import Invalid, Loop


def flatten(
    zone: dict[str, tuple[str, object]], start: str
) -> tuple[str, list[str], object]:
    seen: set[str] = set()
    chain: list[str] = []
    current = start
    while True:
        if current in seen:
            raise Loop(
                f"the CNAME chain returns to {current}; an alias "
                "loop would be followed forever"
            )
        seen.add(current)
        if current not in zone:
            raise Invalid(
                f"{current} is outside this zone; a CNAME to "
                "another zone is a referral to chase, not data to "
                "flatten here"
            )
        kind, payload = zone[current]
        if kind == "cname":
            chain.append(current)
            current = str(payload)
        elif kind == "data":
            return current, chain, payload
        else:
            raise Invalid(f"{kind!r} is not a zone entry kind")
