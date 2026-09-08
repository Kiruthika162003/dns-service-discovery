"""Instance metadata: the tags that route, and the ones that only accrete.

Registered instances carry metadata beyond their address:
version, zone, capabilities, canary flags, and clients select
on it, routing only to instances whose tags satisfy a
predicate. The power is real and so is the rot: tag schemas
have no garbage collector, so a tag added for one migration
outlives it and lingers on every instance forever, and a
client selecting on a tag that no instance sets anymore gets
an empty result that looks like an outage. This module does
selection as set logic and keeps the audit the schema needs
and never gets on its own: the always-true audit names tags
every instance carries identically, which are pure overhead
in every selection because they narrow nothing, the fossil of
a migration that finished without anyone removing its flag.
Selection refuses a predicate referencing a tag key no
instance defines, because that is not a narrow result, it is
a typo, and returning empty for a typo trains clients to
distrust empty, which is the one thing an empty result must
never do.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing


@dataclass
class MetadataRegistry:
    instances: dict[str, dict[str, str]] = field(
        default_factory=dict
    )

    def register(
        self, instance: str, tags: dict[str, str]
    ) -> None:
        if instance in self.instances:
            raise Invalid(f"{instance} already registered")
        self.instances[instance] = dict(tags)

    def _known_keys(self) -> set[str]:
        keys: set[str] = set()
        for tags in self.instances.values():
            keys.update(tags)
        return keys

    def select(self, predicate: dict[str, str]) -> list[str]:
        if not self.instances:
            raise Missing("no instances registered")
        unknown = set(predicate) - self._known_keys()
        if unknown:
            raise Invalid(
                f"selection references tag(s) {sorted(unknown)} "
                "no instance defines; an empty result for a "
                "typo trains clients to distrust empty"
            )
        return sorted(
            instance
            for instance, tags in self.instances.items()
            if all(
                tags.get(key) == value
                for key, value in predicate.items()
            )
        )

    def always_true_audit(self) -> list[str]:
        if len(self.instances) < 2:
            return []
        findings = []
        for key in sorted(self._known_keys()):
            values = {
                tags.get(key) for tags in self.instances.values()
            }
            if len(values) == 1 and None not in values:
                findings.append(
                    f"{key} carries one value on every "
                    "instance; pure overhead in selection "
                    "because it narrows nothing"
                )
        return findings

    def schema_report(self) -> str:
        overhead = self.always_true_audit()
        keys = len(self._known_keys())
        line = (
            f"{len(self.instances)} instance(s), {keys} tag "
            f"key(s), {len(overhead)} narrowing nothing"
        )
        for finding in overhead:
            line += f"\n  {finding}"
        return line
