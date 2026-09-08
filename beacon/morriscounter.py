"""Morris counter: count into the billions using a byte, by only sometimes counting.

An exact counter needs bits proportional to the logarithm of the
count, thirty-two bits to reach a few billion, and when there are
enormous numbers of counters, one per flow, per key, that adds up. A
Morris counter approximates the count in far less, bits proportional
to the logarithm of the logarithm, by storing not the count but an
exponent. Instead of incrementing every time, it increments the
stored exponent only with a probability that halves each time the
exponent grows, so early events almost always bump it and later ones
rarely do, and the estimated count is two to the exponent minus one.
The effect is that a counter which would need thirty-two bits to hold
its true value fits in a single byte, at the cost that the count is
now a random estimate with a relative error rather than an exact
number. That is the right trade for order-of-magnitude telemetry,
roughly how many, and the wrong one wherever an exact count matters.
The probabilistic increment is driven by an injected draw so the
behavior is testable, and the module increments with that
probability, reports the estimate, and refuses a draw outside the
unit interval that names no probability.
"""

from __future__ import annotations

from beacon.errors import Invalid


class MorrisCounter:
    def __init__(self) -> None:
        self.exponent = 0

    def increment(self, draw: float) -> None:
        if not 0.0 <= draw < 1.0:
            raise Invalid(
                f"the draw {draw} must be in [0, 1); it is compared "
                "against the increment probability"
            )
        if draw < 2.0 ** (-self.exponent):
            self.exponent += 1

    def estimate(self) -> int:
        return 2**self.exponent - 1
