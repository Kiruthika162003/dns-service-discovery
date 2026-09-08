"""Split horizon: one name, two truths, and the asker decides which.

A corporate zone answers www.corp.example with a private
address inside the building and a public one outside, and the
mechanism is the view: each view carries a match list of
source networks and its own set of records, evaluated first
match wins, with the catch-all view last. The discipline this
module enforces is the one that saves the three a.m. debug:
every answer is stamped with the view that produced it,
because two engineers comparing dig outputs from home and
office are looking at different truths, and without the stamp
they will file a bug against the resolver instead of noticing
the buildings. Overlapping match lists are the silent hazard,
a network matched by two views gets whichever came first, so
the linter reports shadowed view entries the way a policy
stack would, with the shadower named, since order-dependent
truth should at least know its own order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing


def _network_covers(network: str, address: str) -> bool:
    if network == "any":
        return True
    prefix = network.split("/", maxsplit=1)[0]
    bits = int(network.split("/")[1])
    octets_needed = bits // 8
    net_octets = prefix.split(".")[:octets_needed]
    addr_octets = address.split(".")[:octets_needed]
    return net_octets == addr_octets


@dataclass
class View:
    name: str
    match_networks: tuple[str, ...]
    answers: dict[str, str] = field(default_factory=dict)

    def matches(self, source: str) -> bool:
        return any(
            _network_covers(network, source)
            for network in self.match_networks
        )


@dataclass
class SplitHorizon:
    views: list[View] = field(default_factory=list)

    def add_view(self, view: View) -> None:
        if any(
            held.name == view.name for held in self.views
        ):
            raise Invalid(f"view {view.name} already exists")
        self.views.append(view)

    def answer(self, name: str, source: str) -> str:
        for view in self.views:
            if view.matches(source):
                value = view.answers.get(name)
                if value is None:
                    raise Missing(
                        f"{name} has no answer in view "
                        f"{view.name}, and the view stamp is "
                        "the debugging clue"
                    )
                return (
                    f"{name} = {value} [view: {view.name}]; "
                    "stamped, because two dig outputs from "
                    "two buildings are two truths"
                )
        raise Missing(
            f"{source} matches no view; a horizon without a "
            "catch-all leaves strangers unanswered"
        )

    def shadow_lint(self) -> str:
        shadows = []
        for index, view in enumerate(self.views):
            for earlier in self.views[:index]:
                overlap = [
                    network
                    for network in view.match_networks
                    if any(
                        other in (network, "any")
                        for other in earlier.match_networks
                    )
                ]
                for network in overlap:
                    shadows.append(
                        f"view {view.name} entry {network} is "
                        f"shadowed by view {earlier.name}; "
                        "order-dependent truth should know "
                        "its own order"
                    )
        if not shadows:
            return "no shadowed entries; each network has one truth"
        return "\n".join(
            [f"{len(shadows)} shadowed entrie(s):"]
            + [f"  {line}" for line in shadows]
        )
