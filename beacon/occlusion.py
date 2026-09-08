"""Occlusion: records below a delegation point are shadowed by the child zone.

When a parent zone delegates a subdomain with NS records, the
authority for everything at and below that cut moves to the
child, and any records the parent still holds under the delegated
name become occluded, present in the parent's file but never
served, because the delegation says to ask elsewhere. The classic
trap is glue that has drifted: the parent keeps address records
for a name inside the delegated child so a resolver can reach the
child's servers, but if such a name is not one of the delegated
servers, or sits below the cut for no reason, it is occluded data
the parent must never answer authoritatively. Occlusion is not an
error the server raises, it is an answer the server silently
declines to give, which is exactly why it hides bugs: the records
look configured and pass a file check, yet vanish in production.
The module takes a delegation point and a set of names and reports
which are occluded and which survive as permitted glue, so the
silent decline becomes a visible list.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _is_at_or_below(name: str, point: str) -> bool:
    name = name.rstrip(".")
    point = point.rstrip(".")
    return name == point or name.endswith("." + point)


def is_occluded(
    name: str, point: str, glue_names: set[str]
) -> bool:
    if not _is_at_or_below(name, point):
        return False
    if name.rstrip(".") == point.rstrip("."):
        return False
    return name not in glue_names


def occluded_names(
    names: set[str], point: str, glue_names: set[str]
) -> list[str]:
    if not point.endswith("."):
        raise Invalid(f"the delegation point {point!r} must be dot-rooted")
    for glue in glue_names:
        if not _is_at_or_below(glue, point):
            raise Invalid(
                f"{glue} is named as glue for {point} but lies "
                "outside it; only in-bailiwick names need glue, "
                "and out-of-zone glue is a separate mistake"
            )
    return sorted(
        name
        for name in names
        if is_occluded(name, point, glue_names)
    )


def report(
    names: set[str], point: str, glue_names: set[str]
) -> str:
    hidden = occluded_names(names, point, glue_names)
    return (
        f"below {point}: {len(hidden)} name(s) occluded and "
        f"never served, {len(glue_names)} kept as permitted "
        "glue; the occluded records look configured but vanish "
        "in production"
    )
