"""Bounded clock skew: a lease read is safe only within the assumed clock drift.

A leader can serve linearizable reads without a heartbeat round if
it holds a lease, a promise that no other node will become leader
before a certain time, so within the lease it may answer from local
state and skip the round trip that ReadIndex pays. The catch is
that a lease is a statement about time, and the nodes measuring it
do not share a perfect clock. If the leader's clock runs slow
relative to a peer's, the leader may believe its lease is still
valid after a new leader has already been elected on the peer's
faster clock, and it would then serve a stale read as if it were
current. The defense is to assume a bound on how far the clocks can
drift apart and to treat the lease as expiring that whole bound
early, so the leader stops serving with a margin of safety before
any peer could possibly have moved on. The safety therefore rests
entirely on the skew assumption being true: if real drift exceeds
the bound, the guarantee is void. The module decides whether a
lease read is safe at a given moment under a stated maximum skew,
and refuses a negative skew, since a bound below zero assumes clocks
agree better than perfectly, which is nonsense.
"""

from __future__ import annotations

from beacon.errors import Invalid


def lease_read_safe(
    lease_expiry: int, now: int, max_skew: int
) -> bool:
    if max_skew < 0:
        raise Invalid(
            "a maximum skew below zero assumes the clocks agree "
            "better than perfectly, which is nonsense"
        )
    return now + max_skew < lease_expiry


def safe_until(lease_expiry: int, max_skew: int) -> int:
    if max_skew < 0:
        raise Invalid("a maximum skew is never negative")
    return lease_expiry - max_skew
