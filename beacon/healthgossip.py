"""Health dissemination cost: epidemic spread beats the star that centralizes it.

A registry can learn instance health two ways. Centralized:
every instance reports to one coordinator, which is simple and
makes the coordinator both a bottleneck and a single point of
failure, its inbound load scaling linearly with the fleet.
Epidemic: instances gossip health to a few random peers each
round, and a health change reaches everyone in a number of
rounds that grows only logarithmically with the fleet, at the
cost of redundant messages that carry news a peer already
knew. This module models both and measures the tradeoff the
architecture decision actually turns on: rounds-to-converge
and total messages for a health change across fleet sizes.
The measured surprise the drill preserves is that epidemic's
message count is higher than the star's per event, not lower,
so gossip does not win on total traffic, it wins on the
absence of a bottleneck and the graceful degradation the star
cannot offer, and a team choosing gossip for message
efficiency chose it for the wrong reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class DisseminationModel:
    fleet: int
    fanout: int = 3

    def __post_init__(self) -> None:
        if self.fleet < 2:
            raise Invalid("dissemination needs a fleet to spread across")
        if self.fanout < 1:
            raise Invalid("a fanout of zero spreads nothing")

    def star_messages(self) -> int:
        return self.fleet - 1

    def star_bottleneck_load(self) -> int:
        return self.fleet - 1

    def epidemic_rounds(self) -> int:
        return max(
            1, math.ceil(math.log(self.fleet, self.fanout + 1))
        )

    def epidemic_messages(self) -> int:
        return self.epidemic_rounds() * self.fleet * self.fanout

    def tradeoff_report(self) -> str:
        star = self.star_messages()
        rounds = self.epidemic_rounds()
        epidemic = self.epidemic_messages()
        return (
            f"fleet {self.fleet}: the star sends {star} "
            f"message(s) through one bottleneck of {star}; "
            f"gossip converges in {rounds} round(s) using "
            f"{epidemic} message(s), more traffic, not less, "
            "so gossip wins on the absent bottleneck, not on "
            "message count"
        )


def scaling_table(fleets: list[int]) -> str:
    if not fleets:
        raise Invalid("no fleet sizes to compare")
    lines = ["fleet: star bottleneck vs gossip rounds"]
    for fleet in fleets:
        model = DisseminationModel(fleet=fleet)
        lines.append(
            f"  {fleet}: bottleneck {model.star_bottleneck_load()}, "
            f"gossip rounds {model.epidemic_rounds()}"
        )
    lines.append(
        "the bottleneck grows linearly, the rounds "
        "logarithmically; that gap is the whole argument"
    )
    return "\n".join(lines)
