"""Graceful weight draining: ramp an instance down, not off, before it leaves.

Yanking an instance to zero weight in one step is a small
version of the connection-drain problem: in-flight requests
finish, but the sudden weight shift dumps the instance's share
onto its peers as a step function, and a peer already near
capacity meets the step as a spike. Weight draining ramps
instead: the leaving instance's weight steps down over a
window so its traffic bleeds to peers gradually, each step
small enough that no peer sees more than a bounded jump. The
symmetric case is the arrival, a new instance ramped up from
zero rather than handed its full share cold, because a fresh
instance at full weight is a cold cache meeting peak load, the
same spike from the other direction. The planner computes the
per-step weight schedule from the window and reports the
largest single-step shift any peer absorbs, because the whole
point is bounding that number and a drain that does not report
it is just a slower yank.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass
class DrainPlan:
    instance: str
    start_weight: int
    steps: int

    def __post_init__(self) -> None:
        if self.start_weight < 1:
            raise Invalid(
                "an instance at zero weight is already drained"
            )
        if self.steps < 1:
            raise Invalid(
                "a drain in zero steps is the yank it replaces"
            )

    def schedule(self) -> list[int]:
        weights = []
        for step in range(1, self.steps + 1):
            remaining = round(
                self.start_weight
                * (self.steps - step)
                / self.steps
            )
            weights.append(remaining)
        return weights

    def largest_peer_shift(self, peer_count: int) -> int:
        if peer_count < 1:
            raise Invalid("traffic must shift onto someone")
        schedule = [self.start_weight, *self.schedule()]
        biggest_drop = max(
            schedule[index] - schedule[index + 1]
            for index in range(len(schedule) - 1)
        )
        return -(-biggest_drop // peer_count)

    def drain_report(self, peer_count: int) -> str:
        shift = self.largest_peer_shift(peer_count)
        return (
            f"{self.instance}: weight {self.start_weight} "
            f"drained over {self.steps} step(s); the largest "
            f"single-step shift any of {peer_count} peer(s) "
            f"absorbs is {shift}, and a drain that does not "
            "report that number is just a slower yank"
        )


def rampup_schedule(target_weight: int, steps: int) -> list[int]:
    if target_weight < 1 or steps < 1:
        raise Invalid("a ramp needs a target and steps")
    return [
        round(target_weight * step / steps)
        for step in range(1, steps + 1)
    ]
