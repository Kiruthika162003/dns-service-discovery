"""Wait-die: prevent deadlock by letting waits run in only one timestamp direction.

Rather than detect deadlocks after they form, the wait-die scheme
prevents them from ever forming, using transaction timestamps
assigned at start, where a smaller timestamp means an older
transaction. When a transaction requests a lock held by another, the
decision depends only on their ages. If the requester is older than
the holder, it is allowed to wait, and if the requester is younger,
it does not wait, it dies, aborting immediately and retrying later
with its original timestamp. The rule guarantees no deadlock because
waiting can only go from older to younger, never the reverse, so the
wait-for relation can never form a cycle: a cycle would need some
younger transaction waiting on an older one, which the scheme
forbids. The cost is that younger transactions are aborted even when
no actual deadlock would have occurred, so prevention trades
unnecessary aborts for the guarantee that the system never hangs,
which is the opposite balance from detection. Keeping the original
timestamp on retry matters, because it makes the aborted transaction
progressively older and eventually the oldest, so it is not starved
by repeated deaths. The module decides wait or die from the two
timestamps and confirms the resulting relation is acyclic.
"""

from __future__ import annotations

from beacon.errors import Invalid


def wait_die(requester_ts: int, holder_ts: int) -> str:
    if requester_ts == holder_ts:
        raise Invalid(
            "two transactions share a timestamp; wait-die needs a "
            "strict order to break, so timestamps must be unique"
        )
    if requester_ts < holder_ts:
        return "wait"
    return "die"


def waits_only_old_to_young(requester_ts: int, holder_ts: int) -> bool:
    return wait_die(requester_ts, holder_ts) != "wait" or (
        requester_ts < holder_ts
    )
