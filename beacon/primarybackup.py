"""Primary-backup replication: synchronous loses no data but waits, asynchronous is fast.

A primary that replicates to a backup must decide when to acknowledge
the client, and the decision is the whole durability story.
Synchronous replication waits for the backup to confirm the write
before telling the client it succeeded, so if the primary then dies
the backup already has the write and failover loses nothing, at the
cost that every write pays the round trip to the backup, adding its
latency to the client's. Asynchronous replication acknowledges the
client as soon as the primary has the write and ships it to the
backup in the background, so writes are fast, but a primary that dies
with writes not yet shipped loses them, and failover to the backup
silently rolls those writes back, a data-loss window bounded by how
far behind the backup was. The choice is the classic one between a
recovery point objective of zero and low latency, and it cannot be
had both ways over a real network with real failures. The module
computes the acknowledgement latency each mode imposes and the
data-loss window each exposes on a primary failure, so the trade is
two numbers, the latency paid every write and the writes at risk on a
crash, rather than an unexamined default.
"""

from __future__ import annotations

from beacon.errors import Invalid


def ack_latency(primary_ms: int, backup_ms: int, synchronous: bool) -> int:
    if primary_ms < 0 or backup_ms < 0:
        raise Invalid("latencies are never negative")
    return primary_ms + backup_ms if synchronous else primary_ms


def data_loss_window(unreplicated_writes: int, synchronous: bool) -> int:
    if unreplicated_writes < 0:
        raise Invalid("a count of writes is never negative")
    return 0 if synchronous else unreplicated_writes
