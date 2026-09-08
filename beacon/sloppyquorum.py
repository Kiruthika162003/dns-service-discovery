"""Sloppy quorum: keep writes available during a partition by accepting substitute nodes.

A strict quorum write needs acknowledgements from W of a key's N home
replicas, which guarantees that a later read quorum overlaps the
write, but it also means that if too many home replicas are
unreachable, during a partition or a burst of failures, the write
simply fails, and for many systems refusing the write is worse than
weakening its consistency. A sloppy quorum keeps the write available
by relaxing which nodes may answer. When fewer than W home replicas
are reachable, the coordinator accepts acknowledgements from other
nodes outside the home set, which store the write as a hint and hand
it off to the rightful home replica once it returns, so the write
still collects W acks and succeeds. The cost is a consistency window
that the module names: those substitute acks live on nodes that are
not where a reader looks, so a read from the home replicas can miss
the write until the hinted handoff completes, which strict quorum
would never allow. The module decides whether a write reaches W under
strict and under sloppy rules and reports whether substitutes were
needed, so the availability gained and the consistency briefly given
up are both explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def strict_succeeds(home_acks: int, w: int) -> bool:
    if w < 1:
        raise Invalid("a write quorum of zero acknowledges nothing")
    return home_acks >= w


def sloppy_succeeds(home_acks: int, substitute_acks: int, w: int) -> bool:
    if w < 1:
        raise Invalid("a write quorum of zero acknowledges nothing")
    return home_acks + substitute_acks >= w


def needed_substitutes(home_acks: int, w: int) -> int:
    return max(0, w - home_acks)


def has_consistency_window(home_acks: int, w: int) -> bool:
    return home_acks < w
