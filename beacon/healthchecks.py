"""Health checks with hysteresis: one bad probe is weather, five are climate.

A health checker that flips state on every probe turns a
flaky network path into a strobe light, and downstream systems
amplify every flip into connection churn. Hysteresis is the
cure and it is asymmetric on purpose: marking an instance
unhealthy takes a streak of failures because single failures
are weather, but marking it healthy again takes a longer
streak of successes, because the cost of flapping back too
early, real requests dying on a half-recovered instance, is
paid by users while the cost of waiting is paid in idle
capacity, and those prices are not symmetric. The transition
log keeps every flip with the streak that earned it, and the
flap report names instances whose transition count is out of
line, since a backend that changed state nine times in a
window is not sick or healthy, it is a coin, and coins get
pulled from rotation for diagnosis rather than balanced
around.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

DOWN_AFTER = 3
UP_AFTER = 5
FLAP_ALARM = 4


@dataclass
class CheckedInstance:
    instance_id: str
    healthy: bool = True
    fail_streak: int = 0
    pass_streak: int = 0
    transitions: list[str] = field(default_factory=list)

    def observe(self, passed: bool, now: int) -> str:
        if passed:
            self.pass_streak += 1
            self.fail_streak = 0
            if (
                not self.healthy
                and self.pass_streak >= UP_AFTER
            ):
                self.healthy = True
                self.transitions.append(
                    f"[{now}] up after {self.pass_streak} "
                    "passes"
                )
                return (
                    f"{self.instance_id} recovered: "
                    f"{UP_AFTER} passes earned it, because "
                    "flapping back early kills real requests"
                )
            return f"{self.instance_id} pass"
        self.fail_streak += 1
        self.pass_streak = 0
        if self.healthy and self.fail_streak >= DOWN_AFTER:
            self.healthy = False
            self.transitions.append(
                f"[{now}] down after {self.fail_streak} fails"
            )
            return (
                f"{self.instance_id} marked unhealthy: one "
                "bad probe is weather, "
                f"{DOWN_AFTER} are climate"
            )
        return f"{self.instance_id} fail ({self.fail_streak})"


@dataclass
class HealthBoard:
    instances: dict[str, CheckedInstance] = field(
        default_factory=dict
    )

    def track(self, instance_id: str) -> None:
        if instance_id in self.instances:
            raise Invalid(f"{instance_id} is already tracked")
        self.instances[instance_id] = CheckedInstance(
            instance_id=instance_id
        )

    def observe(
        self, instance_id: str, passed: bool, now: int
    ) -> str:
        held = self.instances.get(instance_id)
        if held is None:
            raise Invalid(f"{instance_id} is not tracked")
        return held.observe(passed, now)

    def flap_report(self) -> str:
        coins = [
            (
                held.instance_id,
                len(held.transitions),
            )
            for held in self.instances.values()
            if len(held.transitions) >= FLAP_ALARM
        ]
        if not coins:
            return "no coins on the board; states are earned"
        lines = [
            f"{len(coins)} instance(s) flipping like coins:"
        ]
        for instance_id, flips in sorted(coins):
            lines.append(
                f"  {instance_id}: {flips} transition(s); "
                "pulled for diagnosis, not balanced around"
            )
        return "\n".join(lines)
