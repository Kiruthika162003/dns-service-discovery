"""NSEC zone walking: the next-name pointer that proves absence also enumerates the zone.

Authenticated denial of existence has to prove a signed negative,
that a name really is not in the zone, and NSEC does it by signing
the gaps: each NSEC record says here is a name that exists and the
next name that exists after it in sorted order, so a query for
anything between them is provably absent because a signed record
swears nothing lives there. The mechanism is sound and it has an
unintended gift for an attacker. Because every NSEC record names the
next existing name, a walker can start anywhere, read the next name,
query it, read its next name, and so on around the whole zone,
enumerating every name it contains without ever guessing, turning
authenticated denial into a directory listing. NSEC3 was the
response: it sorts and points among hashes of the names rather than
the names themselves, so a walk yields a list of hashes instead of
names, which an attacker must still crack offline, raising the cost
without changing that the chain is walkable at all. The module walks
an NSEC next-name chain to show the full enumeration it leaks, and
reports whether a given denial scheme exposes plaintext names or
only hashes.
"""

from __future__ import annotations

from beacon.errors import Invalid, Loop


def walk(next_name: dict[str, str], start: str) -> list[str]:
    if start not in next_name:
        raise Invalid(
            f"{start} is not in the NSEC chain, so the walk has no "
            "place to begin"
        )
    enumerated = [start]
    seen = {start}
    current = next_name[start]
    while current != start:
        if current in seen:
            raise Loop(
                "the NSEC chain revisits a name without closing on "
                "the start; it is malformed, not a zone"
            )
        if current not in next_name:
            raise Invalid(
                f"the chain reaches {current}, which points nowhere; "
                "a dangling next-name is a broken chain, not a zone"
            )
        seen.add(current)
        enumerated.append(current)
        current = next_name[current]
    return enumerated


def leaks_plaintext_names(scheme: str) -> bool:
    if scheme not in ("NSEC", "NSEC3"):
        raise Invalid(f"{scheme!r} is not a denial scheme this reasons about")
    return scheme == "NSEC"
