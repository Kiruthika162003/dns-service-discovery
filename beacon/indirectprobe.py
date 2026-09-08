"""Indirect probing: ask others to reach a member before declaring it gone.

A single failed ping is weak evidence, because far more often than
a node being dead it means the one link between prober and target
dropped a packet, and a failure detector that convicted on one
missed ack would flap healthy members out of the cluster every
time the network hiccupped. SWIM's indirect probe strengthens the
evidence cheaply. When a direct ping goes unanswered the prober
does not conclude anything; it asks k other members to ping the
same target on its behalf, and if any of them gets an ack the
target is alive and it was the prober's own path that was bad. Only
when the direct probe and all k indirect probes fail does the
target become a suspect, and that agreement across independent
paths is what makes the conviction trustworthy: the chance that k
plus one distinct paths all fail at once for a live node is the
product of their individual drop rates, vanishingly smaller than
any one path failing. The module reports the verdict and computes
that compounded false-positive probability so the fan-out k is
chosen against a target error rate rather than by feel.
"""

from __future__ import annotations

from beacon.errors import Invalid


def verdict(direct_ack: bool, indirect_acks: list[bool]) -> str:
    if direct_ack:
        return "alive-direct"
    if any(indirect_acks):
        return "alive-indirect"
    return "suspect"


def false_positive_rate(
    per_link_drop: float, fanout: int
) -> float:
    if not 0.0 <= per_link_drop <= 1.0:
        raise Invalid(
            f"a per-link drop rate of {per_link_drop} is not a "
            "probability between zero and one"
        )
    if fanout < 0:
        raise Invalid("the fan-out cannot be negative")
    return per_link_drop ** (fanout + 1)


def fanout_for_target(
    per_link_drop: float, target_rate: float
) -> int:
    if not 0.0 < per_link_drop < 1.0:
        raise Invalid(
            "the per-link drop rate must be strictly between zero "
            "and one to reduce a target by adding paths"
        )
    fanout = 0
    while false_positive_rate(per_link_drop, fanout) > target_rate:
        fanout += 1
    return fanout
