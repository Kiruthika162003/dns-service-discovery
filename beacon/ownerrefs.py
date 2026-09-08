"""Owner references: delete a service and its endpoints follow, but an unowned object leaks.

A service in a registry owns dependent objects, the endpoint records
that point at its backends, and deleting the service should delete
those endpoints too or they dangle, pointing at a service that no
longer exists. Owner references automate the cascade. Each dependent
object records which objects own it, and a garbage collector treats
an object as collectible once it has owners and every one of them is
gone, so deleting the last owner sweeps the dependents without the
client having to track and delete them by hand. The mechanism has a
sharp edge the module makes visible: an object with no owner
references at all is a root, never garbage, so if a dependent is
created without its owner reference set, deleting the owner leaves
the dependent behind as an orphan that no cascade will ever reach,
a leak that accumulates silently. The module computes, from a set of
objects and their owner references and a set of deleted owners,
which objects have become garbage and which were orphaned by a
missing reference, so the automatic cleanup and its one failure mode
are both explicit rather than assumed.
"""

from __future__ import annotations


def collectible(
    objects: dict[str, set[str]], existing_owners: set[str]
) -> set[str]:
    return {
        name
        for name, owners in objects.items()
        if owners and owners.isdisjoint(existing_owners)
    }


def orphans(objects: dict[str, set[str]]) -> set[str]:
    return {name for name, owners in objects.items() if not owners}
