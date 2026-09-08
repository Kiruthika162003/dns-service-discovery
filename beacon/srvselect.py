"""SRV selection: priority is an order, weight is a proportion, and they do not mix.

An SRV record set is not a flat list of interchangeable
endpoints; it is a two-level plan. Priority is absolute: every
record at the lowest priority is tried before any record at a
higher one, so priority is failover, a strict order the client
must honor. Weight is proportional and only within a priority:
among the records that share the lowest priority, the client
picks one with probability proportional to its weight, so weight
is load spreading, not ordering. Collapsing the two, treating a
higher weight as if it were a higher priority, is the common
error, and it defeats the design: the operator used priority to
say try these first and weight to say split the load among them,
and a client that sorted purely by weight would send traffic to
a backup tier while the primary sat idle. A target of the single
dot is the explicit refusal, the service declaring it is not
offered here, and the module treats it as such rather than
dialing a root.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid, Refused


@dataclass(frozen=True)
class SrvRecord:
    priority: int
    weight: int
    target: str
    port: int

    def __post_init__(self) -> None:
        if self.weight < 0 or self.priority < 0:
            raise Invalid(
                "SRV priority and weight are unsigned; a "
                "negative value is not a valid preference"
            )


def _lowest_group(records: list[SrvRecord]) -> list[SrvRecord]:
    offered = [r for r in records if r.target != "."]
    if not offered:
        raise Refused(
            "every SRV target is the root dot; the service is "
            "explicitly declaring it is not offered here"
        )
    lowest = min(r.priority for r in offered)
    group = [r for r in offered if r.priority == lowest]
    return sorted(group, key=lambda r: (r.weight, r.target))


def select(records: list[SrvRecord], draw: int) -> SrvRecord:
    if not records:
        raise Invalid("an empty SRV set names no service to try")
    group = _lowest_group(records)
    total = sum(r.weight for r in group)
    if total == 0:
        return group[draw % len(group)]
    point = draw % total
    running = 0
    for record in group:
        running += record.weight
        if point < running:
            return record
    return group[-1]


def failover_order(records: list[SrvRecord]) -> list[int]:
    offered = [r for r in records if r.target != "."]
    return sorted({r.priority for r in offered})
