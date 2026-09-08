"""Following an HTTPS alias chain: bounded hops and a visited set, or the records loop forever.

An HTTPS record in AliasMode points at another target name, which
may itself hold an AliasMode record pointing somewhere else, so
resolving a name to its actual service endpoint means walking a
chain of aliases until one lands on a ServiceMode record that
describes a real endpoint. A chain is a graph a zone operator
controls, and a graph can be made to bite: a record whose alias
points back to a name already visited forms a cycle that a naive
follower walks forever, and even without a cycle an
adversarially long chain can exhaust a resolver's patience one hop
at a time. So a follower needs two guards, a visited set to catch a
cycle the moment it returns to a name it has already passed
through, and a hop limit to bound a chain that does not loop but
simply runs too long. The module walks the alias map from a start
name, returns the ServiceMode endpoint the chain terminates at,
raises on a revisited name as the loop it is, and refuses a chain
that exceeds the hop bound rather than following an alias graph
built to waste the resolver.
"""

from __future__ import annotations

from beacon.errors import Invalid, Loop


def resolve_endpoint(
    aliases: dict[str, str | None], start: str, max_hops: int = 8
) -> str:
    seen: set[str] = set()
    current = start
    hops = 0
    while aliases.get(current) is not None:
        if current in seen:
            raise Loop(
                f"the alias chain returns to {current}; a cycle in "
                "the HTTPS records would be followed forever"
            )
        seen.add(current)
        current = aliases[current]
        hops += 1
        if hops > max_hops:
            raise Invalid(
                f"the alias chain exceeds {max_hops} hops; a chain "
                "this long is either a mistake or built to waste "
                "the resolver, and either way it is refused"
            )
    return current
