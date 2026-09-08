"""Server selection by smoothed RTT: ask the fastest, but keep checking the rest.

A resolver with four upstreams learns their speed the only way
that stays true, by asking, and remembers it as a smoothed
round-trip time: each new sample moves the estimate a fraction
of the way, so one slow answer nudges rather than slanders and
one fast answer earns rather than crowns. Selection prefers
the lowest estimate, which raises the starvation trap the
decay solves: a server that was slow once would never be asked
again and never get the chance to disprove the record, so
every unasked server's estimate decays toward optimism each
round, guaranteeing even the disgraced an occasional retrial.
Timeouts are punished harder than slowness, entered as a
multiple of the timeout rather than the timeout itself,
because a server that answered slowly told the truth slowly
while a server that never answered wasted the full wait and
told nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing

ALPHA = 0.3
DECAY = 0.98
TIMEOUT_PENALTY = 3


@dataclass
class UpstreamRecord:
    name: str
    srtt: float = 50.0


@dataclass
class Selector:
    upstreams: dict[str, UpstreamRecord] = field(
        default_factory=dict
    )
    retrials_granted: int = 0

    def add(self, name: str) -> None:
        if name in self.upstreams:
            raise Invalid(f"{name} is already an upstream")
        self.upstreams[name] = UpstreamRecord(name=name)

    def choose(self) -> str:
        if not self.upstreams:
            raise Missing("no upstreams to choose from")
        return min(
            self.upstreams.values(),
            key=lambda held: (held.srtt, held.name),
        ).name

    def observe(
        self, name: str, rtt: float | None, timeout_at: float = 200.0
    ) -> str:
        held = self.upstreams.get(name)
        if held is None:
            raise Missing(f"{name} is not an upstream")
        if rtt is None:
            sample = timeout_at * TIMEOUT_PENALTY
            held.srtt = (
                held.srtt * (1 - ALPHA) + sample * ALPHA
            )
            self._decay_others(name)
            return (
                f"{name} timed out: entered as "
                f"{sample:.0f}, because a slow answer told "
                "the truth slowly and a timeout told nothing"
            )
        if rtt < 0:
            raise Invalid("negative round trips break physics")
        held.srtt = held.srtt * (1 - ALPHA) + rtt * ALPHA
        self._decay_others(name)
        return f"{name}: srtt now {held.srtt:.1f}"

    def _decay_others(self, asked: str) -> None:
        for held in self.upstreams.values():
            if held.name != asked:
                before = held.srtt
                held.srtt *= DECAY
                if before > 100 and held.srtt <= 100:
                    self.retrials_granted += 1

    def standings(self) -> str:
        rows = sorted(
            self.upstreams.values(),
            key=lambda held: (held.srtt, held.name),
        )
        lines = ["the standings, fastest first:"]
        for held in rows:
            lines.append(f"  {held.name}: {held.srtt:.1f}")
        lines.append(
            f"{self.retrials_granted} retrial(s) granted by "
            "decay; even the disgraced get asked again"
        )
        return "\n".join(lines)
