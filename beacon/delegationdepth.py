"""Bounded delegation depth: a resolver must cap how deep it will chase before giving up.

Recursive resolution follows delegations downward, root to top-level
domain to zone to sub-zone, each referral pointing one level closer
to the answer, and in a healthy namespace the chain is short. But a
resolver cannot assume health, because a misconfigured or malicious
namespace can present an endless staircase of delegations, each zone
delegating to a deeper one that never actually holds the answer, and
a resolver that followed without limit would spend itself walking a
staircase built to exhaust it. So resolution carries a depth budget,
a maximum number of referrals it will follow before it stops and
returns a failure rather than chase further. The bound also guards
the related danger of a referral that points sideways or back up
into a loop, which the depth limit catches even when cycle detection
does not, because a loop simply runs the counter out. Setting the
bound is a small trade, high enough that every legitimate name in a
deep but real hierarchy resolves, low enough that a hostile chain is
abandoned quickly. The module tracks the depth of a resolution and
refuses to descend past the bound, naming the runaway chain rather
than following it into the ground.
"""

from __future__ import annotations

from beacon.errors import Invalid, Loop


class Descent:
    def __init__(self, max_depth: int = 16) -> None:
        if max_depth < 1:
            raise Invalid(
                "a depth budget below one cannot follow even a "
                "single delegation; resolution would answer nothing"
            )
        self.max_depth = max_depth
        self.depth = 0

    def follow_referral(self) -> int:
        self.depth += 1
        if self.depth > self.max_depth:
            raise Loop(
                f"resolution followed {self.depth} referrals past "
                f"the {self.max_depth} budget; the chain is a "
                "staircase built to exhaust the resolver, not a path "
                "to an answer"
            )
        return self.depth

    def remaining(self) -> int:
        return self.max_depth - self.depth
