"""Active health checks with rise and fall thresholds, so a flapping backend stays put.

An active health check probes a backend and decides whether it is in
or out of the load-balancing pool, and doing that on a single probe
is a mistake in both directions: one failed probe on a healthy
backend, a dropped packet, would eject it needlessly, and one lucky
success on a broken backend would readmit it prematurely. Rise and
fall thresholds add the hysteresis that fixes both. A backend already
out of the pool must pass a number of consecutive probes, the rise
threshold, before it is readmitted, so a single fluke success does
not bring a still-broken backend back, and a backend in the pool must
fail a number of consecutive probes, the fall threshold, before it is
ejected, so a single fluke failure does not remove a healthy one. The
two thresholds can differ deliberately, often a low fall to eject a
truly failing backend quickly and a higher rise to make sure it has
really recovered before trusting it with traffic. A success resets
the failure streak and a failure resets the success streak, so only
consecutive results count. The module runs the state machine over a
sequence of probe results and reports the pool membership, so the
hysteresis is a decidable state rather than a guess.
"""

from __future__ import annotations

from beacon.errors import Invalid


class HealthCheck:
    def __init__(
        self, rise: int, fall: int, healthy: bool = True
    ) -> None:
        if rise < 1 or fall < 1:
            raise Invalid(
                "rise and fall thresholds must be at least one; a "
                "threshold of zero would flip on no evidence"
            )
        self.rise = rise
        self.fall = fall
        self.healthy = healthy
        self.consecutive_ok = 0
        self.consecutive_fail = 0

    def record(self, ok: bool) -> None:
        if ok:
            self.consecutive_ok += 1
            self.consecutive_fail = 0
            if not self.healthy and self.consecutive_ok >= self.rise:
                self.healthy = True
        else:
            self.consecutive_fail += 1
            self.consecutive_ok = 0
            if self.healthy and self.consecutive_fail >= self.fall:
                self.healthy = False

    def in_pool(self) -> bool:
        return self.healthy
