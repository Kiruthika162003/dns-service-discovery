"""GCD, LCM, and the hyperperiod: the schedule length that certifies a periodic system forever.

A set of periodic tasks, each repeating on its own period, has a
schedule that eventually repeats as a whole, and the length of that
repeating block is the hyperperiod, the least common multiple of all
the periods. It matters because verifying a real-time schedule over
one hyperperiod certifies it for all time: if every deadline is met
through one full block, the identical block that follows meets them
too, forever, so an exhaustive check need only run that far. The
least common multiple rests on the greatest common divisor, which the
Euclidean algorithm computes by repeatedly replacing the larger
number with its remainder on division by the smaller until one
reaches zero, and the least common multiple of two numbers is their
product divided by that divisor. The honest catch the module surfaces
is that the hyperperiod can explode: when periods share few factors,
being pairwise coprime in the extreme, the least common multiple is
nearly their product, so a handful of awkward periods can make the
hyperperiod astronomically long and the exhaustive check
intractable, which is exactly why real-time designers choose harmonic
periods, each a multiple of the next, that keep the hyperperiod
small. The module computes the greatest common divisor, the least
common multiple, and the hyperperiod of a set of periods, refusing a
non-positive period that has no cycle.
"""

from __future__ import annotations

from beacon.errors import Invalid


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    if a <= 0 or b <= 0:
        raise Invalid("a period must be positive to have a cycle")
    return a * b // gcd(a, b)


def hyperperiod(periods: list[int]) -> int:
    if not periods:
        raise Invalid("no periods; there is no schedule to repeat")
    result = 1
    for period in periods:
        result = lcm(result, period)
    return result
