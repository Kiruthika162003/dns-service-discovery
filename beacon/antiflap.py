"""Flap damping: a route that keeps flapping accrues a penalty and is held down until it decays.

A backend or route that oscillates, up and down and up again
every few seconds, is worse than one that is simply down, because
each transition forces the whole system to reconverge, and a
storm of flaps can consume more capacity in bookkeeping than the
traffic itself. Flap damping, borrowed from BGP, taxes
instability. Each flap adds to a penalty that decays exponentially
over time, and once the penalty crosses a suppress threshold the
route is held down and ignored regardless of its current state,
staying suppressed until the penalty decays back below a separate,
lower reuse threshold. The two thresholds are deliberately
different, and that gap is the point: if the route came back the
instant it dropped below the suppress level it would immediately
be eligible to flap again, so the lower reuse threshold forces the
penalty to decay well past the danger line before the route is
trusted, buying hysteresis. The module refuses a reuse threshold
at or above the suppress threshold, since that erases the
hysteresis and lets a route chatter right at the boundary.
"""

from __future__ import annotations

from beacon.errors import Invalid


class FlapDamper:
    def __init__(
        self,
        penalty_per_flap: float = 1.0,
        suppress_threshold: float = 3.0,
        reuse_threshold: float = 1.5,
        half_life: float = 15.0,
    ) -> None:
        if reuse_threshold >= suppress_threshold:
            raise Invalid(
                "the reuse threshold must sit below the suppress "
                "threshold; equal thresholds erase the hysteresis "
                "and let the route chatter at the boundary"
            )
        if half_life <= 0:
            raise Invalid(
                "the half-life must be positive or the penalty "
                "never decays and a route once suppressed stays "
                "dead forever"
            )
        self.penalty_per_flap = penalty_per_flap
        self.suppress_threshold = suppress_threshold
        self.reuse_threshold = reuse_threshold
        self.half_life = half_life
        self.penalty = 0.0
        self.suppressed = False

    def flap(self) -> None:
        self.penalty += self.penalty_per_flap
        if self.penalty >= self.suppress_threshold:
            self.suppressed = True

    def decay(self, elapsed: float) -> None:
        self.penalty *= 0.5 ** (elapsed / self.half_life)
        if self.suppressed and self.penalty < self.reuse_threshold:
            self.suppressed = False

    def usable(self) -> bool:
        return not self.suppressed
