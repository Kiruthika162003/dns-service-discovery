"""Raft log matching: refuse an append whose predecessor disagrees, and the logs converge.

Raft keeps every follower's log identical to the leader's by
enforcing one property on every append: an entry is accepted only
if the entry immediately before it, identified by its index and
term, matches what the follower already has at that position. That
single boundary check is enough because of an inductive guarantee
it maintains, that if two logs agree on an entry then they agree on
every entry before it, so matching the one predecessor certifies
the entire prefix without re-sending it. When the predecessor does
not match, the follower is either behind, with a gap where the
predecessor should be, in which case the leader must back up and
resend from earlier, or it holds a conflicting entry from a
different term, in which case that entry and everything after it is
wrong and must be truncated before the new entries are written. The
module models the follower's append: it refuses a gap, truncates a
conflicting suffix, and writes the entries so the log matches the
leader's from the checked point forward, which is how divergent
followers are pulled back into agreement one append at a time.
"""

from __future__ import annotations

from beacon.errors import Refused


def append(
    log_terms: list[int],
    prev_index: int,
    prev_term: int,
    entries: list[int],
) -> list[int]:
    if prev_index < 0:
        raise Refused("a previous index is never negative")
    if prev_index > len(log_terms):
        raise Refused(
            f"the log has {len(log_terms)} entries but the append "
            f"assumes {prev_index} before it; the follower is "
            "behind and the leader must back up and resend"
        )
    if prev_index > 0 and log_terms[prev_index - 1] != prev_term:
        raise Refused(
            f"the entry at index {prev_index} is term "
            f"{log_terms[prev_index - 1]}, not the {prev_term} the "
            "leader expects; this is a conflict to truncate, not an "
            "append to apply"
        )
    return log_terms[:prev_index] + entries
