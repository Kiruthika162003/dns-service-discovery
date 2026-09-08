"""Empty non-terminals exist: a name with children answers NODATA, never NXDOMAIN.

If x.a.b.example. holds a record then a.b.example. and b.example.
exist as names even when they carry no records of their own,
because a name in the tree cannot have a child and yet not exist.
These are empty non-terminals, and the distinction they force is
between NXDOMAIN, meaning this name is nowhere in the zone, and
NODATA, meaning the name exists but holds no record of the type
asked. A resolver that returned NXDOMAIN for an empty
non-terminal would be lying twice: it would tell the client a
name does not exist while a child of it plainly does, and
negative caching would then remember that lie and poison every
future query for anything under that name. The module walks the
set of owner names, derives every ancestor a child implies, and
classifies a query as NODATA when the name is present as an empty
non-terminal or a differently-typed owner, and NXDOMAIN only when
neither the name nor any descendant of it appears at all.
"""

from __future__ import annotations

from beacon.errors import Invalid, Missing


def implied_names(owners: set[str], apex: str) -> set[str]:
    if not apex.endswith("."):
        raise Invalid(f"the apex {apex!r} must be dot-rooted")
    names = {apex}
    apex_labels = apex.rstrip(".").split(".")
    for owner in owners:
        labels = owner.rstrip(".").split(".")
        if labels[-len(apex_labels) :] != apex_labels:
            raise Invalid(
                f"{owner} is not within the zone {apex}; it "
                "cannot imply names in a zone it does not belong to"
            )
        for start in range(len(labels) - len(apex_labels) + 1):
            names.add(".".join(labels[start:]) + ".")
    return names


def classify(
    qname: str,
    qtype: str,
    records: dict[tuple[str, str], list[str]],
    owners: set[str],
    apex: str,
) -> str:
    if (qname, qtype) in records:
        return "answer"
    if qname in implied_names(owners, apex):
        return "nodata"
    raise Missing(
        f"{qname} is nowhere in {apex} and no descendant of it "
        "exists; this is NXDOMAIN, not the NODATA an empty "
        "non-terminal would earn"
    )
