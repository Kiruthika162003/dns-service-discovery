"""Gossip membership: rumors spread, suspicion has a deadline, death is refuted.

A cluster cannot ask everyone about everyone every tick, so
membership travels as rumor: each round, every member tells a
few peers what it believes, and beliefs carry incarnation
numbers so newer testimony beats older no matter the path it
took. The state machine is SWIM's: alive, suspected, dead. A
missed probe raises suspicion, never a death sentence, because
the difference between a dead process and a slow network is
invisible from one vantage point; suspicion has a deadline,
and only its expiry declares death. The refutation rule is the
protocol's soul: a suspected member that hears its own obituary
increments its incarnation and gossips the denial, and the
higher incarnation beats the suspicion everywhere it has
spread, which is how a slow-but-alive member survives a
network sneeze without an operator noticing anything at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing

SUSPICION_TICKS = 5


@dataclass
class Belief:
    state: str
    incarnation: int
    suspected_at: int | None = None


@dataclass
class MemberView:
    owner: str
    beliefs: dict[str, Belief] = field(default_factory=dict)
    refutations: int = 0

    def join(self, member: str) -> None:
        if member in self.beliefs:
            raise Invalid(f"{member} already joined this view")
        self.beliefs[member] = Belief(state="alive", incarnation=0)

    def _held(self, member: str) -> Belief:
        belief = self.beliefs.get(member)
        if belief is None:
            raise Missing(f"{member} is a stranger to {self.owner}")
        return belief

    def probe_missed(self, member: str, now: int) -> str:
        belief = self._held(member)
        if belief.state == "dead":
            return f"{member} is already mourned"
        if belief.state == "suspected":
            return f"{member} is already under suspicion"
        belief.state = "suspected"
        belief.suspected_at = now
        return (
            f"{member} suspected at {now}: a missed probe is "
            "never a death sentence, because a dead process and "
            "a slow network look identical from here"
        )

    def sweep(self, now: int) -> list[str]:
        declared = []
        for member, belief in self.beliefs.items():
            if (
                belief.state == "suspected"
                and now - belief.suspected_at >= SUSPICION_TICKS
            ):
                belief.state = "dead"
                belief.suspected_at = None
                declared.append(
                    f"{member} declared dead: the suspicion "
                    f"deadline of {SUSPICION_TICKS} expired "
                    "unrefuted"
                )
        return declared

    def refute_own_death(self, now: int) -> tuple[int, str]:
        belief = self._held(self.owner)
        belief.incarnation += 1
        belief.state = "alive"
        belief.suspected_at = None
        self.refutations += 1
        return belief.incarnation, (
            f"{self.owner} heard its own obituary and answers "
            f"with incarnation {belief.incarnation}; newer "
            "testimony beats older everywhere it spreads"
        )

    def receive_gossip(
        self, member: str, state: str, incarnation: int, now: int
    ) -> str:
        belief = self.beliefs.get(member)
        if belief is None:
            self.beliefs[member] = Belief(
                state=state,
                incarnation=incarnation,
                suspected_at=now if state == "suspected" else None,
            )
            return f"{member} learned of via rumor: {state}"
        if incarnation < belief.incarnation:
            return (
                f"stale rumor about {member} discarded: "
                f"incarnation {incarnation} lost to "
                f"{belief.incarnation}"
            )
        if incarnation > belief.incarnation:
            belief.incarnation = incarnation
            belief.state = state
            belief.suspected_at = (
                now if state == "suspected" else None
            )
            return (
                f"{member}: newer incarnation {incarnation} "
                f"overrules; now {state}"
            )
        rank = {"alive": 0, "suspected": 1, "dead": 2}
        if rank[state] > rank[belief.state]:
            belief.state = state
            belief.suspected_at = (
                now if state == "suspected" else None
            )
            return (
                f"{member}: same incarnation, graver news "
                f"wins; now {state}"
            )
        return f"{member}: nothing new"

    def roster(self) -> str:
        counts = {"alive": 0, "suspected": 0, "dead": 0}
        for belief in self.beliefs.values():
            counts[belief.state] += 1
        return (
            f"{self.owner} sees {counts['alive']} alive, "
            f"{counts['suspected']} suspected, "
            f"{counts['dead']} dead; {self.refutations} "
            "obituary(ies) refuted"
        )
