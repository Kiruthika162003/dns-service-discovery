"""Failover with a split-brain guard: promote the passive only when the active is truly gone.

Active-passive failover sounds simple, promote the passive when the
active dies, but the hard part is telling death from a lost
connection. If the passive promotes itself merely because it can no
longer reach the active, and the active is in fact alive on the other
side of a network partition, both now believe they are active, both
serve writes, and the data diverges: split brain, the worst outcome
of a failover done too eagerly. The guard is to require independent
confirmation before promoting. The passive may promote only when two
things hold: the active is observed unhealthy, and an independent
witness, a quorum, a third party that both can reach, confirms the
active is genuinely down rather than merely unreachable from the
passive. If the passive cannot reach the witness either, it must not
promote, because it cannot distinguish the active being dead from
itself being the partitioned one, and promoting on that ambiguity is
exactly how split brain happens. The trade is that failover waits for
the witness, so a failover is a little slower for being safe, which is
the right side of the trade when the alternative is two active writers.
The module decides whether to promote, refusing on ambiguity.
"""

from __future__ import annotations

from beacon.errors import Refused


def should_promote(
    active_healthy: bool, witness_reachable: bool, witness_confirms_dead: bool
) -> bool:
    if active_healthy:
        return False
    if not witness_reachable:
        raise Refused(
            "the active looks unreachable but the witness is "
            "unreachable too; the passive cannot tell the active is "
            "dead from itself being partitioned, and promoting on "
            "that ambiguity is how split brain happens"
        )
    return witness_confirms_dead
