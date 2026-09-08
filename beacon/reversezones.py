"""Reverse zones: the address asks for its name, and drift tells on itself.

Forward records map names to addresses; the reverse tree maps
addresses back, spelled octet-reversed under in-addr.arpa, and
nothing in the protocol forces the two to agree. The
synthesizer builds the reverse zone from the forward records
so they agree by construction, one PTR per address with the
forward name as its target, and collisions are surfaced
rather than resolved silently: two forward names on one
address is legal and common, but the PTR can only point one
way, so the synthesizer requires an explicit choice and
records it, because a reverse chosen by iteration order is a
coin toss that mail servers will later grade. The drift audit
is the operational tool: given a reverse zone maintained by
hand, it names every mismatch against the forward truth in
both directions, the PTR pointing at a name that no longer
holds the address, and the address whose PTR simply never got
written.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


def reverse_name(address: str) -> str:
    octets = address.split(".")
    if len(octets) != 4:
        raise Invalid(
            f"{address!r} is not a dotted quad; the reverse "
            "tree has no floor for it"
        )
    return ".".join(reversed(octets)) + ".in-addr.arpa."


@dataclass
class ReverseSynthesizer:
    forward: dict[str, str] = field(default_factory=dict)
    chosen: dict[str, str] = field(default_factory=dict)

    def add_forward(self, name: str, address: str) -> None:
        self.forward[name] = address

    def choose_canonical(self, address: str, name: str) -> None:
        if self.forward.get(name) != address:
            raise Invalid(
                f"{name} does not hold {address}; a canonical "
                "choice must pick among the truth"
            )
        self.chosen[address] = name

    def synthesize(self) -> dict[str, str]:
        by_address: dict[str, list[str]] = {}
        for name, address in self.forward.items():
            by_address.setdefault(address, []).append(name)
        zone: dict[str, str] = {}
        for address, names in sorted(by_address.items()):
            if len(names) == 1:
                zone[reverse_name(address)] = names[0]
                continue
            choice = self.chosen.get(address)
            if choice is None:
                raise Invalid(
                    f"{address} is held by "
                    f"{', '.join(sorted(names))} and the PTR "
                    "points one way; choose, because a "
                    "reverse picked by iteration order is a "
                    "coin toss mail servers will grade"
                )
            zone[reverse_name(address)] = choice
        return zone

    def drift_audit(
        self, hand_maintained: dict[str, str]
    ) -> list[str]:
        truth = self.synthesize()
        findings = []
        for ptr, target in sorted(hand_maintained.items()):
            expected = truth.get(ptr)
            if expected is None:
                findings.append(
                    f"{ptr} -> {target}: points at a world "
                    "the forward zone no longer describes"
                )
            elif expected != target:
                findings.append(
                    f"{ptr}: hand says {target}, forward "
                    f"truth says {expected}"
                )
        for ptr, target in sorted(truth.items()):
            if ptr not in hand_maintained:
                findings.append(
                    f"{ptr} -> {target}: never written by "
                    "hand; the address answers to nobody"
                )
        return findings
