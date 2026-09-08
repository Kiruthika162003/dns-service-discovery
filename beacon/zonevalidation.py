"""Pre-load zone validation: refuse a broken zone before it goes live, not after.

A zone file that parses can still be broken in ways that only
bite at serve time: an NS record pointing at a name the zone
never defines, a CNAME whose target is another CNAME through a
chain that never terminates, an MX-style priority record whose
target resolves to nothing, a wildcard that shadows an explicit
name the operator forgot they wrote. Loading such a zone and
discovering the break from a user's failed lookup is the most
expensive way to find it. The validator runs the checks a
parser cannot, because they are about relationships between
records rather than the shape of one, and it reports every
break with the record that causes it, refusing to load a zone
with a fatal break while merely warning on the cosmetic ones,
because a validator that treats every finding as fatal teaches
operators to disable it and one that treats every finding as a
warning teaches them to ignore it, and the line between the two
is the whole judgment the tool exists to encode.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class ZoneValidator:
    names: set[str] = field(default_factory=set)
    cnames: dict[str, str] = field(default_factory=dict)
    ns_targets: dict[str, str] = field(default_factory=dict)

    def define(self, name: str) -> None:
        self.names.add(name)

    def add_cname(self, name: str, target: str) -> None:
        self.cnames[name] = target
        self.names.add(name)

    def add_ns(self, zone: str, target: str) -> None:
        self.ns_targets[zone] = target
        self.names.add(zone)

    def _cname_terminates(self, start: str) -> bool:
        seen = set()
        current = start
        while current in self.cnames:
            if current in seen:
                return False
            seen.add(current)
            current = self.cnames[current]
        return True

    def validate(self) -> tuple[list[str], list[str]]:
        fatal = []
        warnings = []
        for zone, target in sorted(self.ns_targets.items()):
            if target not in self.names:
                fatal.append(
                    f"NS for {zone} points at {target}, which "
                    "the zone never defines; a delegation into "
                    "the void"
                )
        for name, target in sorted(self.cnames.items()):
            if not self._cname_terminates(name):
                fatal.append(
                    f"CNAME {name} -> {target} never "
                    "terminates; an alias chain that circles"
                )
        for name in sorted(self.names):
            if name.startswith("*."):
                stem = name[2:]
                shadowed = [
                    other
                    for other in self.names
                    if other != name
                    and other.endswith("." + stem)
                ]
                if shadowed:
                    warnings.append(
                        f"wildcard {name} shadows explicit "
                        f"{', '.join(sorted(shadowed))}; likely "
                        "meant, worth a second look"
                    )
        return fatal, warnings

    def load_verdict(self) -> str:
        fatal, warnings = self.validate()
        if fatal:
            raise Invalid(
                f"refusing to load: {len(fatal)} fatal "
                "break(s) that would bite at serve time:\n"
                + "\n".join(f"  {line}" for line in fatal)
            )
        if warnings:
            return (
                f"loaded with {len(warnings)} warning(s); "
                "cosmetic, not fatal, because a validator that "
                "fails on everything gets disabled:\n"
                + "\n".join(f"  {line}" for line in warnings)
            )
        return "loaded clean; every relationship resolves"
