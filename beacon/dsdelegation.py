"""The chain of trust: the parent vouches for the child, or the child is an orphan.

Signed zones do not trust each other directly; each parent
holds a fingerprint of its child's signing key, and validation
walks that chain from a root everyone trusts down to the
answer. The break this module models is the single most common
signed-zone outage: a child rotates its signing key and does
not update the fingerprint at its parent, so the child's
signatures are perfectly valid and perfectly unvouched-for, an
orphan whose papers do not match the record on file. The
checker walks the chain and names exactly where trust breaks,
distinguishing the three failure shapes an operator must tell
apart: the missing link where a parent holds no fingerprint at
all, the stale link where the fingerprint does not match the
child's current key, and the broken root where the top of the
chain is not one the validator was configured to trust. Each
gets a different fix and the same refusal to guess which.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class SignedZone:
    name: str
    key_fingerprint: str
    parent: str | None


@dataclass
class TrustChain:
    zones: dict[str, SignedZone] = field(default_factory=dict)
    parent_records: dict[str, str] = field(default_factory=dict)
    trusted_roots: set[str] = field(default_factory=set)

    def add_zone(
        self,
        name: str,
        key_fingerprint: str,
        parent: str | None,
    ) -> None:
        if name in self.zones:
            raise Invalid(f"{name} already in the chain")
        self.zones[name] = SignedZone(
            name=name,
            key_fingerprint=key_fingerprint,
            parent=parent,
        )

    def publish_ds(self, child: str, fingerprint: str) -> None:
        if child not in self.zones:
            raise Invalid(f"{child} is not a signed zone")
        self.parent_records[child] = fingerprint

    def trust_root(self, name: str) -> None:
        self.trusted_roots.add(name)

    def validate(self, name: str) -> str:
        current = name
        hops = []
        while True:
            zone = self.zones.get(current)
            if zone is None:
                raise Invalid(
                    f"{current} is not a signed zone in the "
                    "chain"
                )
            hops.append(current)
            if zone.parent is None:
                if current in self.trusted_roots:
                    return (
                        f"{name}: trust chain intact through "
                        f"{len(hops)} zone(s) to the trusted "
                        f"root {current}"
                    )
                return (
                    f"BROKEN ROOT: {current} tops the chain "
                    "but is not a configured trust anchor; "
                    "the whole chain floats"
                )
            on_file = self.parent_records.get(current)
            if on_file is None:
                return (
                    f"MISSING LINK: {zone.parent} holds no "
                    f"fingerprint for {current}; the child is "
                    "unvouched-for, an orphan with no papers"
                )
            if on_file != zone.key_fingerprint:
                return (
                    f"STALE LINK: {current} rotated its key to "
                    f"{zone.key_fingerprint[:8]} but "
                    f"{zone.parent} still vouches for "
                    f"{on_file[:8]}; valid signatures nobody "
                    "vouches for, the commonest signed-zone "
                    "outage"
                )
            current = zone.parent
