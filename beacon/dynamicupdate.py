"""Dynamic update: prerequisites checked as one gate, then the change, or nothing.

RFC 2136 lets a client add and delete records in a live zone,
and the danger it must survive is the lost update: two clients
read the zone, each decides a change, and the second write
clobbers the first without ever seeing it. The prerequisite
section is the guard against that. A client states what it
believes the zone contains, an RRset present, an RRset absent, a
name in use, a name free, and the server checks every
prerequisite before applying any change, so the update commits
only against the exact state the client saw. If a single
prerequisite is false the whole update is refused with the
reason named, YXDOMAIN for a name that should have been free,
NXRRSET for a set that should have existed, and nothing is
written, because a half-applied update against a stale belief is
precisely the corruption the prerequisites exist to prevent. The
update itself is applied to a copy and swapped in at the end, so
a failure midway through leaves the zone as it was.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class MutableZone:
    rrsets: dict[tuple[str, str], set[str]] = field(
        default_factory=dict
    )

    def rrset_exists(self, name: str, rrtype: str) -> bool:
        return bool(self.rrsets.get((name, rrtype)))

    def name_in_use(self, name: str) -> bool:
        return any(
            key[0] == name and values
            for key, values in self.rrsets.items()
        )


def _check_one(zone: MutableZone, prereq: tuple) -> None:
    kind, name, rrtype = prereq
    if kind == "rrset-exists":
        if not zone.rrset_exists(name, rrtype):
            raise Invalid(
                f"NXRRSET: prerequisite failed, {name} has no "
                f"{rrtype} set the update was written against"
            )
    elif kind == "rrset-absent":
        if zone.rrset_exists(name, rrtype):
            raise Invalid(
                f"YXRRSET: prerequisite failed, {name} already "
                f"has a {rrtype} set that should have been absent"
            )
    elif kind == "name-in-use":
        if not zone.name_in_use(name):
            raise Invalid(
                f"NXDOMAIN: prerequisite failed, {name} is not "
                "in use but the update assumed it was"
            )
    elif kind == "name-free":
        if zone.name_in_use(name):
            raise Invalid(
                f"YXDOMAIN: prerequisite failed, {name} is in "
                "use but the update assumed it was free"
            )
    else:
        raise Invalid(f"{kind} is not a prerequisite kind")


def apply_update(
    zone: MutableZone,
    prerequisites: list[tuple],
    updates: list[tuple],
) -> MutableZone:
    for prereq in prerequisites:
        _check_one(zone, prereq)
    draft = {
        key: set(values) for key, values in zone.rrsets.items()
    }
    for update in updates:
        op = update[0]
        if op == "add":
            _, name, rrtype, value = update
            draft.setdefault((name, rrtype), set()).add(value)
        elif op == "delete-rrset":
            _, name, rrtype = update
            draft.pop((name, rrtype), None)
        elif op == "delete":
            _, name, rrtype, value = update
            if (name, rrtype) in draft:
                draft[(name, rrtype)].discard(value)
                if not draft[(name, rrtype)]:
                    draft.pop((name, rrtype))
        else:
            raise Invalid(f"{op} is not an update operation")
    return MutableZone(draft)
