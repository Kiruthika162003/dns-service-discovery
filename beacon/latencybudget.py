"""The resolution latency budget: every hop spends time nobody accounted for.

A page load waits on a name resolution, and the resolution's
latency is a sum of parts operators rarely itemize until it is
slow: the cache lookup, the network round trips to authorities,
the CNAME chain that adds a lookup each, the DNSSEC validation
that adds signature checks. The budget models the resolution as
a line-itemed sum against a target, because a resolution over
budget is diagnosed by which line dominates, not by staring at
the total, and the three fixes live in three different places:
a network-bound resolution wants a nearer resolver, a chain-
bound one wants the CNAMEs flattened, a validation-bound one
wants the crypto cached. The report ranks the parts by their
share and names the dominant one with its fix, because a team
that optimizes the second-biggest line because it is easier is
tuning for effort, not for latency, and the itemized budget is
what stops that.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class ResolutionCost:
    cache_lookup: int
    network_round_trips: int
    cname_hops: int
    validation_checks: int

    ROUND_TRIP = 25
    HOP_COST = 20
    CHECK_COST = 5

    def parts(self) -> dict[str, int]:
        return {
            "cache": self.cache_lookup,
            "network": self.network_round_trips * self.ROUND_TRIP,
            "cname": self.cname_hops * self.HOP_COST,
            "validation": (
                self.validation_checks * self.CHECK_COST
            ),
        }

    def total(self) -> int:
        return sum(self.parts().values())


FIXES = {
    "cache": "a warmer cache; the lookup itself should be free",
    "network": "a nearer resolver; the round trips dominate",
    "cname": "flatten the CNAME chain; each hop is a lookup",
    "validation": "cache the crypto; signatures recheck needlessly",
}


def budget_report(cost: ResolutionCost, target: int) -> str:
    if target < 1:
        raise Invalid("a target of zero is not a budget")
    total = cost.total()
    parts = cost.parts()
    dominant = max(parts, key=lambda name: (parts[name], name))
    over = total > target
    lines = [
        f"resolution {total} tick(s) against a {target} "
        f"budget: {'OVER' if over else 'within'}"
    ]
    for name in sorted(parts, key=lambda n: -parts[n]):
        share = 100 * parts[name] // max(total, 1)
        lines.append(f"  {name}: {parts[name]} ({share}%)")
    if over:
        lines.append(
            f"the dominant line is {dominant}; the fix is "
            f"{FIXES[dominant]}, not the second-biggest line "
            "because it is easier"
        )
    return "\n".join(lines)
