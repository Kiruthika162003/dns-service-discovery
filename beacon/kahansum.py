"""Kahan summation: recover the rounding error each addition throws away.

Adding a long list of floating-point numbers the obvious way lets a
tiny rounding error creep in at every step, and when the running total
grows large while the incoming terms stay small, each new term can be
rounded almost entirely away, so a naive fold can silently lose most of
what it was meant to add. Kahan summation fixes this by carrying a
second small running value, a compensation, that holds the low-order
part the last addition could not fit. Before each term is added the
compensation is subtracted back in, and after the addition the algorithm
recovers exactly how much was lost by rearranging the same operations,
and stashes that loss in the compensation for next time. The effect is a
sum whose error does not grow with the length of the list, bought for a
few extra arithmetic operations per element. The honest context is worth
stating plainly: CPython's own built-in sum adopted a related
compensated scheme in version 3.12, so this is not faster than the
builtin on floats, and where the very last drop of accuracy matters the
exactly-rounded math.fsum is better still. What this module offers is the
explicit algorithm as a reusable, inspectable building block, correct
against a naive fold and clear about how the compensation works. It sums
a list of numbers and refuses nothing, treating the empty list as zero.
"""

from __future__ import annotations


def kahan_sum(values: list[float]) -> float:
    total = 0.0
    compensation = 0.0
    for value in values:
        adjusted = value - compensation
        tentative = total + adjusted
        compensation = (tentative - total) - adjusted
        total = tentative
    return total
