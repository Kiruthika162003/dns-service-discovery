"""Topology spread: place replicas evenly across failure domains so one zone loss is survivable.

Putting several replicas of a service on the same rack or in the same
zone defeats the point of replication, because the failure that
matters, a rack losing power, a zone partitioning, takes them all at
once. Topology spread places replicas across failure domains so that
no single domain holds too many, quantified by a maximum skew, the
allowed difference between the most and least occupied domain. The
placement that minimizes skew is greedy and simple: assign each
replica to the domain that currently holds the fewest, so the counts
stay as level as the number of replicas and domains allows. The honest
limit the module surfaces is that the constraint and availability can
conflict. If there are too few domains to spread the replicas within
the max skew, the scheduler faces a choice it cannot dodge, place a
replica in violation of the spread or leave it unscheduled, and
pretending both the skew and the replica count can always be honored
is how a scheduler wedges. The module distributes replicas greedily
across the domains including any already placed, measures the
resulting skew, and decides whether a max-skew constraint is
satisfied, so the tension is explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def distribute(
    replicas: int, domains: list[str], existing: dict[str, int] | None = None
) -> dict[str, int]:
    if replicas < 0:
        raise Invalid("a negative replica count is not a placement")
    if not domains:
        raise Invalid("no failure domains to spread across")
    counts = dict.fromkeys(domains, 0)
    if existing:
        for domain, count in existing.items():
            if domain not in counts:
                raise Invalid(
                    f"{domain} holds replicas but is not among the "
                    "spread domains; the topology is inconsistent"
                )
            counts[domain] = count
    for _ in range(replicas):
        least = min(domains, key=lambda d: (counts[d], d))
        counts[least] += 1
    return counts


def skew(counts: dict[str, int]) -> int:
    if not counts:
        return 0
    return max(counts.values()) - min(counts.values())


def satisfies(counts: dict[str, int], max_skew: int) -> bool:
    if max_skew < 0:
        raise Invalid("a max skew is never negative")
    return skew(counts) <= max_skew
