"""Maintenance windows: planned absence that does not page the on-call.

An instance taken down for a deploy is healthy in every sense
that matters and dead to every health check, so a registry
without a maintenance concept pages the on-call for work the
operator scheduled on purpose. The maintenance window is the
fix: an instance enters maintenance, is removed from rotation
without alarms, and its failed health checks are expected
rather than paged. The discipline this module enforces is the
expiry: a window has a declared end, and an instance still in
maintenance past its window is escalated, because the most
common real outage hiding behind a maintenance flag is the
deploy that hung and nobody noticed, the instance parked in
maintenance forever while its capacity silently left the
fleet. The report separates planned absence from overrun,
because a fleet with three instances in maintenance is fine
and a fleet with three instances overrun is three capacity
losses wearing a planned-work costume.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing


@dataclass
class Window:
    instance: str
    started: int
    ends_at: int
    reason: str


@dataclass
class MaintenanceBoard:
    windows: dict[str, Window] = field(default_factory=dict)

    def enter(
        self,
        instance: str,
        now: int,
        duration: int,
        reason: str,
    ) -> str:
        if instance in self.windows:
            raise Invalid(
                f"{instance} is already in maintenance"
            )
        if duration < 1:
            raise Invalid(
                "a zero-duration window is not maintenance, "
                "it is a flicker"
            )
        if not reason.strip():
            raise Invalid(
                "maintenance without a reason is an outage "
                "someone forgot to declare"
            )
        self.windows[instance] = Window(
            instance=instance,
            started=now,
            ends_at=now + duration,
            reason=reason,
        )
        return (
            f"{instance} in maintenance until {now + duration}: "
            "failed checks expected, not paged"
        )

    def leave(self, instance: str) -> str:
        if instance not in self.windows:
            raise Missing(f"{instance} was not in maintenance")
        del self.windows[instance]
        return f"{instance} back in rotation"

    def is_expected_down(self, instance: str, now: int) -> bool:
        window = self.windows.get(instance)
        return window is not None and now < window.ends_at

    def board_report(self, now: int) -> str:
        planned = []
        overrun = []
        for window in self.windows.values():
            if now < window.ends_at:
                planned.append(window.instance)
            else:
                overrun.append(
                    f"{window.instance}: overrun by "
                    f"{now - window.ends_at} tick(s) "
                    f"({window.reason}); the deploy that hung "
                    "and nobody noticed"
                )
        lines = [
            f"{len(planned)} planned absence(s), "
            f"{len(overrun)} overrun(s)"
        ]
        lines.extend(f"  overrun {entry}" for entry in overrun)
        if overrun:
            lines.append(
                "overruns are capacity losses wearing a "
                "planned-work costume, escalate them"
            )
        return "\n".join(lines)
