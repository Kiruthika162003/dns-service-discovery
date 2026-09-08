"""Monotonic reads: once a client has seen a version, it never later sees an older one.

Under replication a client's successive reads can land on different
replicas, and if a later read hits a replica that lags the one an
earlier read hit, the client watches time run backward: a record it
already saw updated reverts to an older value, which is deeply
confusing even though each replica is internally consistent.
Monotonic reads is the session guarantee that forbids it. The
session remembers the highest version the client has observed, and a
replica may serve a read only if its version is at least that high,
so the client's own view of the data never regresses even as it is
bounced between replicas. Enforcing it means a read may have to be
steered away from a replica that is behind the client's watermark
toward one that has caught up, or wait for one to, which is the
availability the guarantee spends to keep the client's timeline
moving forward. The guarantee is per client session and says nothing
about other clients, so it is cheaper than global consistency while
still removing the jarring reversal. The module tracks the session
watermark, decides whether a replica's version is acceptable to
serve, and advances the watermark as the client reads.
"""

from __future__ import annotations


def acceptable(session_watermark: int, replica_version: int) -> bool:
    return replica_version >= session_watermark


def observe(session_watermark: int, read_version: int) -> int:
    return max(session_watermark, read_version)
