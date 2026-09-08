"""Kadane's algorithm: the maximum-sum contiguous subarray in one pass.

Given a sequence of numbers, some positive and some negative, the
maximum-sum contiguous subarray is the run whose total is largest, and
it answers questions like the most profitable window of trades or the
densest stretch of a signal. Checking every possible run is quadratic,
but Kadane's algorithm finds the answer in a single left-to-right pass
on a small realization: the best run ending at a given position is
either that position's value alone or that value joined to the best run
ending just before it, whichever is larger. So it carries one running
sum, extends it when extending helps, and abandons it for a fresh start
whenever the running sum has gone negative and would only drag the next
value down. Tracking the best running sum ever seen, along with where it
began and ended, yields the winning subarray. The honest subtlety is the
all-negative case: if every number is negative there is no positive run,
and the right answer is the single least-negative element rather than an
empty run of sum zero, which this module returns by seeding from the
first element rather than from zero. It refuses an empty sequence, which
has no subarray to speak of.
"""

from __future__ import annotations

from beacon.errors import Invalid


def maximum_subarray(values: list[float]) -> tuple[float, int, int]:
    if not values:
        raise Invalid(
            "the sequence is empty; there is no subarray whose sum to maximize"
        )
    best_sum = values[0]
    best_start = 0
    best_end = 0
    current_sum = values[0]
    current_start = 0
    for index in range(1, len(values)):
        value = values[index]
        if current_sum < 0:
            current_sum = value
            current_start = index
        else:
            current_sum += value
        if current_sum > best_sum:
            best_sum = current_sum
            best_start = current_start
            best_end = index
    return best_sum, best_start, best_end
