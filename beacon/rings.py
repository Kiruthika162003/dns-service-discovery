"""Ring rollouts: the resolver fleet updates in cohorts that earn the next.

Changing resolver config fleet-wide in one push turns every
config mistake into a total outage, so the fleet updates in
rings: a small canary cohort first, then successively larger
rings, each gated on the previous ring baking without
incident for its full bake time. The gate is earned, not
scheduled: a ring advances only when its predecessor's error
budget stayed clean through the bake, and any incident rolls
the change back everywhere, because a config bad for ring
one is bad for ring three with more zeros. The discipline
this module refuses to relax is skipping: no ring may deploy
before its predecessor finishes baking, however urgent the
release feels, since urgency is precisely when mistakes ship,
and the ledger records every completed rollout with its total
elapsed time so the cost of caution is a number the release
manager can weigh instead of a myth they resent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

BAKE_TICKS = 30


@dataclass
class Ring:
    name: str
    size: int
    deployed_at: int | None = None
    baked: bool = False


@dataclass
class RingRollout:
    change: str
    rings: list[Ring] = field(default_factory=list)
    rolled_back: bool = False
    history: list[str] = field(default_factory=list)

    def add_ring(self, name: str, size: int) -> None:
        if self.rings and size <= self.rings[-1].size:
            raise Invalid(
                f"{name} at {size} is not larger than its "
                "predecessor; rings grow or they are just "
                "batches"
            )
        self.rings.append(Ring(name=name, size=size))

    def _next_undeployed(self) -> Ring | None:
        for ring in self.rings:
            if ring.deployed_at is None:
                return ring
        return None

    def deploy_next(self, now: int) -> str:
        if self.rolled_back:
            raise Invalid(
                f"{self.change} was rolled back; a new "
                "attempt is a new rollout"
            )
        ring = self._next_undeployed()
        if ring is None:
            raise Invalid("every ring is deployed")
        index = self.rings.index(ring)
        if index > 0:
            previous = self.rings[index - 1]
            if not previous.baked:
                raise Invalid(
                    f"{ring.name} may not deploy before "
                    f"{previous.name} finishes baking; "
                    "urgency is precisely when mistakes ship"
                )
        ring.deployed_at = now
        self.history.append(f"[{now}] {ring.name} deployed")
        return (
            f"{ring.name} ({ring.size} resolver(s)) running "
            f"{self.change}; bake until {now + BAKE_TICKS}"
        )

    def report_bake(
        self, ring_name: str, now: int, incident: bool
    ) -> str:
        ring = next(
            (
                held
                for held in self.rings
                if held.name == ring_name
            ),
            None,
        )
        if ring is None or ring.deployed_at is None:
            raise Invalid(f"{ring_name} is not baking")
        if incident:
            self.rolled_back = True
            self.history.append(
                f"[{now}] rollback from {ring_name}"
            )
            return (
                f"ROLLBACK everywhere: a config bad for "
                f"{ring_name} is bad for the last ring with "
                "more zeros"
            )
        if now - ring.deployed_at < BAKE_TICKS:
            return (
                f"{ring_name} still baking "
                f"({now - ring.deployed_at} of {BAKE_TICKS})"
            )
        ring.baked = True
        return f"{ring_name} baked clean; the next ring is earned"

    def rollout_ledger(self, now: int) -> str:
        if self.rolled_back:
            return (
                f"{self.change}: rolled back; the rings "
                "caught it at "
                f"{self.rings[0].size} resolver(s) instead "
                "of everywhere"
            )
        if all(ring.baked for ring in self.rings):
            started = int(
                self.history[0].split("]")[0][1:]
            )
            return (
                f"{self.change}: complete in {now - started} "
                "tick(s); the cost of caution is a number, "
                "not a myth to resent"
            )
        return f"{self.change}: in progress"
