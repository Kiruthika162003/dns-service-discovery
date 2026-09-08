"""The watchtower: synthetic queries with expected answers, asked on a schedule.

Monitoring that waits for users to complain measures
complaint latency, not availability. The watchtower asks its
own questions: each probe carries a name, the answer it
expects, and the resolver view it asks through, because a
zone can be healthy inside and broken outside and a probe
that only asks from one building certifies one building. The
grading is strict about kinds of wrong: a missing answer, a
wrong answer, and a slow answer are three different pages,
wrong being the gravest because serving the wrong address is
worse than serving none. The streak rule keeps the pager
honest, one bad probe logs and three page, matching the
health-check hysteresis everywhere else in this repository,
and the coverage report names zones with no probes at all,
since an unwatched zone is not a healthy zone, it is a zone
whose failures report to nobody.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

PAGE_AFTER = 3
SLOW_AT = 50


@dataclass
class Probe:
    name: str
    expected: str
    view: str
    bad_streak: int = 0


@dataclass
class Watchtower:
    probes: dict[str, Probe] = field(default_factory=dict)
    pages_sent: int = 0
    logged_only: int = 0

    def add_probe(
        self, name: str, expected: str, view: str
    ) -> None:
        key = f"{name}@{view}"
        if key in self.probes:
            raise Invalid(f"{key} is already watched")
        self.probes[key] = Probe(
            name=name, expected=expected, view=view
        )

    def observe(
        self,
        name: str,
        view: str,
        answer: str | None,
        latency: int,
    ) -> str:
        key = f"{name}@{view}"
        probe = self.probes.get(key)
        if probe is None:
            raise Invalid(f"{key} is not a watched probe")
        if answer == probe.expected and latency < SLOW_AT:
            probe.bad_streak = 0
            return f"{key}: as expected in {latency}"
        probe.bad_streak += 1
        if answer is None:
            kind = "MISSING"
        elif answer != probe.expected:
            kind = (
                "WRONG, the gravest: serving the wrong "
                "address is worse than serving none"
            )
        else:
            kind = f"SLOW at {latency}"
        if probe.bad_streak >= PAGE_AFTER:
            self.pages_sent += 1
            return (
                f"{key}: {kind}; streak "
                f"{probe.bad_streak}, PAGING"
            )
        self.logged_only += 1
        return (
            f"{key}: {kind}; logged "
            f"({probe.bad_streak}/{PAGE_AFTER}), one bad "
            "probe logs and three page"
        )

    def coverage_report(self, zones: list[str]) -> str:
        watched = {
            probe.name.split(".", 1)[1]
            for probe in self.probes.values()
        }
        unwatched = sorted(
            zone for zone in zones if zone not in watched
        )
        if not unwatched:
            return (
                f"{len(zones)} zone(s), all watched; failures "
                "have somewhere to report"
            )
        lines = [
            f"{len(unwatched)} unwatched zone(s); an "
            "unwatched zone is a zone whose failures report "
            "to nobody:"
        ]
        lines.extend(f"  {zone}" for zone in unwatched)
        return "\n".join(lines)
