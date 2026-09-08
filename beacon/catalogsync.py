"""Cross-cluster catalog federation: your services, mine, and the honest border.

Two datacenters each run a registry, and services in one are
sometimes needed from the other, so registries federate: each
imports a read-only view of the other's catalog. The border is
where federation goes wrong, and this module draws it firmly.
Imported services are namespaced by their origin cluster, so a
billing service in west and a billing service in east never
collide into one confusing set, and a client asking for a
local service never accidentally reaches a remote one that
happens to share a name. Imported entries are never re-exported
onward, because a three-cluster mesh that re-exports would loop
a service's registration around forever, each hop restamping
it, and the import is read-only because writing into a peer's
catalog across the border is how one cluster's bad deploy
becomes another's outage. The report separates local services
from imported ones and names any collision that would have
occurred without namespacing, since the collision the border
prevented is invisible unless the border counts it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class FederatedCatalog:
    cluster: str
    local: set[str] = field(default_factory=set)
    imported: dict[str, str] = field(default_factory=dict)

    def register_local(self, service: str) -> None:
        if service in self.local:
            raise Invalid(f"{service} already local")
        self.local.add(service)

    def import_from(
        self, peer: str, services: list[str]
    ) -> str:
        if peer == self.cluster:
            raise Invalid(
                "a cluster does not import from itself; that is "
                "just its local catalog with extra steps"
            )
        collisions = []
        for service in services:
            key = f"{peer}/{service}"
            self.imported[key] = service
            if service in self.local:
                collisions.append(service)
        note = ""
        if collisions:
            note = (
                f"; namespacing prevented {len(collisions)} "
                "collision(s) with local services of the same "
                "name"
            )
        return (
            f"imported {len(services)} service(s) from {peer} "
            f"read-only, namespaced under {peer}/{note}"
        )

    def resolve(self, query: str) -> str:
        if "/" not in query:
            if query in self.local:
                return f"{query}: local"
            raise Invalid(
                f"{query} is not local; a remote service must "
                "be asked for by its cluster/name, so a local "
                "lookup never reaches a remote namesake"
            )
        if query in self.imported:
            return f"{query}: imported, read-only"
        raise Invalid(f"{query} is not imported here")

    def re_export_check(self, service: str) -> str:
        if service in self.imported:
            raise Invalid(
                f"{service} is imported and cannot be "
                "re-exported; a mesh that re-exports loops a "
                "registration around forever"
            )
        return f"{service} is local and exportable"

    def border_report(self) -> str:
        return (
            f"{self.cluster}: {len(self.local)} local "
            f"service(s), {len(self.imported)} imported "
            "read-only; the border keeps them separate so one "
            "cluster's deploy is not another's outage"
        )
