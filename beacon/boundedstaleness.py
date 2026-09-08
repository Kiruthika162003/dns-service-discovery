"""Bounded staleness: a read may lag the latest write, but by no more than a stated bound.

Strong consistency, where every read sees the very latest write,
forces reads through the leader or a quorum and pays for it in
latency and availability, while eventual consistency lets any
replica answer but places no limit on how far behind it might be, so
a read could reflect a state from an unknown and unbounded time ago.
Bounded staleness is the middle contract that many systems actually
want. A read may be served from a replica that lags the latest
write, keeping it fast and available, but only if the replica is
within a stated bound of the latest, expressed as a number of
versions or a span of time, so the answer is allowed to be old but
never more than the bound old. That turns an unbounded risk into a
knob: tighten the bound toward zero and approach strong consistency
at rising cost, loosen it and serve from more replicas at the price
of more possible staleness. The bound is the explicit trade rather
than a hidden one. The module decides whether a replica is within
the staleness bound of the latest version, reports how stale a
replica is, and refuses a negative bound, which would forbid even a
perfectly current read.
"""

from __future__ import annotations

from beacon.errors import Invalid


def staleness(latest_version: int, replica_version: int) -> int:
    if replica_version > latest_version:
        raise Invalid(
            "a replica cannot be ahead of the latest version; the "
            "staleness would be negative, which is not a lag"
        )
    return latest_version - replica_version


def within_bound(
    latest_version: int, replica_version: int, max_lag: int
) -> bool:
    if max_lag < 0:
        raise Invalid(
            "a negative staleness bound forbids even a current "
            "read; the bound is how old an answer may be, not how "
            "fresh it must be beyond fresh"
        )
    return staleness(latest_version, replica_version) <= max_lag
