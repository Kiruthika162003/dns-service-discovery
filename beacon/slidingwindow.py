"""Sliding window rate limiting: closing the boundary burst a fixed window leaves open.

A fixed-window rate limit is simple and wrong at the seams. It
counts requests in each wall-clock window and resets the count at
the boundary, which means a client can send a full window's worth
of requests in the last instant of one window and another full
window's worth in the first instant of the next, twice the limit
inside a span shorter than a single window, precisely the burst
the limit was meant to forbid. The sliding window fixes it with a
weighted estimate: it keeps the previous window's count and the
current one, and weights the previous count by how much of it
still overlaps the trailing window, so as the current window ages
the previous window's contribution fades smoothly instead of
vanishing at the boundary. The estimate is an approximation, it
assumes the previous window's requests were spread evenly, but it
is bounded and cheap and it removes the doubling, and the module
computes both the fixed count and the sliding estimate so the
boundary burst the fixed window admits is a number next to the
sliding window that refuses it.
"""

from __future__ import annotations

from beacon.errors import Invalid


def fixed_window_allows(count_in_window: int, limit: int) -> bool:
    return count_in_window < limit


def sliding_estimate(
    previous_count: int,
    current_count: int,
    elapsed_fraction: float,
) -> float:
    if not 0.0 <= elapsed_fraction <= 1.0:
        raise Invalid(
            f"the elapsed fraction {elapsed_fraction} is not a "
            "share of the current window between zero and one"
        )
    weight_of_previous = 1.0 - elapsed_fraction
    return previous_count * weight_of_previous + current_count


def sliding_allows(
    previous_count: int,
    current_count: int,
    elapsed_fraction: float,
    limit: int,
) -> bool:
    return (
        sliding_estimate(
            previous_count, current_count, elapsed_fraction
        )
        < limit
    )


def boundary_burst(limit: int) -> str:
    return (
        f"a fixed window admits {limit} at the close of one window "
        f"and {limit} at the open of the next, {2 * limit} inside "
        "one window's span; the sliding estimate weights the "
        "fading previous count and refuses the doubling"
    )
