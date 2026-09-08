"""Glueless delegation: when the parent must ship a nameserver's address, and when it must not.

A delegation names the servers authoritative for a child zone, and
whether the parent must include their addresses as glue turns on
where those servers live. If a nameserver's own name sits inside
the zone being delegated, ns1.child.example under a delegation of
child.example, a resolver cannot look up that name without first
reaching the very servers the delegation points to, a
chicken-and-egg the parent must break by shipping the address as
glue in the delegation itself. But if the nameserver lives in some
other zone, ns1.provider.net, the resolver resolves it the ordinary
way, and the parent must not ship glue for it, because an address
the parent is not authoritative for is unauthenticated data it has
no business asserting and a cache-poisoning surface if it does. So
glue is required for in-bailiwick servers and forbidden for
out-of-zone ones, and the one fatal mistake is an in-bailiwick
nameserver with no glue, a lame delegation that sends every
resolver into the loop the glue exists to break. The module reports
each server's glue status and refuses a delegation whose
in-bailiwick servers lack the glue that makes them reachable.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _in_zone(name: str, zone: str) -> bool:
    name = name.rstrip(".")
    zone = zone.rstrip(".")
    return name == zone or name.endswith("." + zone)


def glue_status(ns_name: str, delegated_zone: str) -> str:
    return "required" if _in_zone(ns_name, delegated_zone) else "forbidden"


def validate_delegation(
    ns_names: list[str],
    delegated_zone: str,
    glue_provided: set[str],
) -> str:
    if not ns_names:
        raise Invalid(
            f"{delegated_zone} is delegated to no nameservers; a "
            "delegation with no NS is not a delegation"
        )
    for ns_name in ns_names:
        if (
            glue_status(ns_name, delegated_zone) == "required"
            and ns_name not in glue_provided
        ):
            raise Invalid(
                f"{ns_name} is in-bailiwick for {delegated_zone} "
                "but has no glue; a resolver cannot reach it "
                "without resolving a name only it can serve, which "
                "is a lame delegation"
            )
    return "delegation reachable"
