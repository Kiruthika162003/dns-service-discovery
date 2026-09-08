"""Serial arithmetic: version numbers on a circle, compared without vertigo.

Zone serials are 32-bit counters that must never stop, so the
protocol makes them circular: 4294967295 plus one is zero, and
"newer" is defined by RFC 1982 as being within the forward
half of the circle. The comparison is the part operators get
wrong twice a decade, once when the date-encoded serial
2026090901 needs to move past a fat-fingered 4000000000, and
once when they discover that two serials exactly half the
circle apart are incomparable by design, neither newer,
because the circle has no way to say which direction is
forward when the distance is a coin flip. This module answers
newer-than honestly, refuses the incomparable pair by name,
and computes the step plan for the fat-finger recovery: the
sequence of publishes that walks a serial the long way around
the circle, each step under the half-circle limit, which is
the documented cure and the reason the arithmetic exists.
"""

from __future__ import annotations

from beacon.errors import Invalid

MODULUS = 2**32
HALF = 2**31


def check_serial(serial: int) -> None:
    if not 0 <= serial < MODULUS:
        raise Invalid(
            f"{serial} does not fit in 32 bits; serials live "
            "on the circle or not at all"
        )


def newer(candidate: int, reference: int) -> bool:
    check_serial(candidate)
    check_serial(reference)
    if candidate == reference:
        return False
    distance = (candidate - reference) % MODULUS
    if distance == HALF:
        raise Invalid(
            f"{candidate} and {reference} sit exactly half the "
            "circle apart; neither is newer, by design, because "
            "forward is a coin flip at that distance"
        )
    return distance < HALF


def bump(serial: int, by: int = 1) -> int:
    check_serial(serial)
    if not 1 <= by < HALF:
        raise Invalid(
            f"a bump of {by} must be positive and under the "
            "half circle, or newer stops meaning anything"
        )
    return (serial + by) % MODULUS


def recovery_plan(current: int, target: int) -> list[int]:
    check_serial(current)
    check_serial(target)
    if current == target:
        raise Invalid("already there; no plan needed")
    try:
        if newer(target, current):
            return [target]
    except Invalid:
        pass
    steps = []
    position = current
    while True:
        distance = (target - position) % MODULUS
        if 0 < distance < HALF:
            steps.append(target)
            return steps
        position = (position + HALF - 1) % MODULUS
        steps.append(position)
        if len(steps) > 4:
            raise Invalid(
                "the plan is circling; the circle is only two "
                "half-steps around"
            )
