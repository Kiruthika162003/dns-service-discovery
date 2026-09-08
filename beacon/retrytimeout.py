"""Retry with two limits: a per-attempt timeout and a total deadline, whichever binds first.

Bounding retries by a count alone is a trap when each attempt is
slow: three retries of a two-second timeout can consume six seconds
against a caller who is only willing to wait three, so the retries
blow the very deadline they were meant to work within, and the caller
gets an error later than if there had been no retry at all. Sound
retry policy carries two limits at once. A maximum retry count caps
how many times it is worth trying, and a total deadline caps how long
the whole effort, first attempt and all retries, may take, and a
retry is allowed only if both permit it: there is a retry left in the
count, and there is enough time before the deadline to run another
full attempt. That second check is the one people forget, because
starting an attempt that cannot finish before the deadline wastes the
time it runs and returns nothing, so the policy must refuse to start
an attempt whose timeout would cross the deadline. The module
computes how many attempts the two limits jointly allow and decides
whether another attempt should start given the elapsed time, so a
slow dependency cannot spend a budget the caller reserved for
itself.
"""

from __future__ import annotations

from beacon.errors import Invalid


def attempts_allowed(
    per_attempt: int, total_deadline: int, max_retries: int
) -> int:
    if per_attempt <= 0 or total_deadline <= 0:
        raise Invalid(
            "the per-attempt timeout and total deadline must be "
            "positive durations"
        )
    if max_retries < 0:
        raise Invalid("a negative retry count is not a limit")
    by_time = total_deadline // per_attempt
    return min(max_retries + 1, by_time)


def should_attempt(
    attempt: int,
    elapsed: int,
    per_attempt: int,
    total_deadline: int,
    max_retries: int,
) -> bool:
    if attempt > max_retries:
        return False
    return elapsed + per_attempt <= total_deadline
