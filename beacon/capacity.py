"""Capacity-aware routing: weight is a guess, load is the ground truth.

Static weights encode capacity the operator believed at
config time, and the belief drifts: a backend on a noisy
neighbor, a backend paging to disk, a backend whose weight
was copied from a bigger box. Capacity-aware routing corrects
the guess with the backend's own reported load, scaling the
effective weight down as a backend approaches its ceiling so
traffic drains off a struggling instance before it tips. The
danger this module refuses is the stampede: if every router
reacts to the same load report at the same instant, they all
flee the busy backend together and flood the next one, so the
correction is damped, a fraction of the gap per interval
rather than the whole gap at once, which converges without
oscillating. The report contrasts the static split against
the load-corrected one on the same backends, because the
whole feature is invisible until the numbers show weight
sending traffic to a backend that measurement says is full.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

DAMPING = 0.5


@dataclass
class Backend:
    name: str
    static_weight: int
    load_fraction: float = 0.0
    effective_weight: float = 0.0

    def __post_init__(self) -> None:
        if self.static_weight < 1:
            raise Invalid(
                f"{self.name}: a zero static weight is drained, "
                "not routed"
            )
        self.effective_weight = float(self.static_weight)


@dataclass
class CapacityRouter:
    backends: dict[str, Backend] = field(default_factory=dict)

    def add(self, name: str, static_weight: int) -> None:
        if name in self.backends:
            raise Invalid(f"{name} already routed")
        self.backends[name] = Backend(
            name=name, static_weight=static_weight
        )

    def report_load(self, name: str, load_fraction: float) -> str:
        backend = self.backends.get(name)
        if backend is None:
            raise Invalid(f"{name} is not routed")
        if not 0 <= load_fraction <= 1:
            raise Invalid("load is a fraction between 0 and 1")
        backend.load_fraction = load_fraction
        target = backend.static_weight * (1 - load_fraction)
        gap = target - backend.effective_weight
        backend.effective_weight += gap * DAMPING
        return (
            f"{name} at {load_fraction:.0%} load: effective "
            f"weight eased toward {target:.0f}, now "
            f"{backend.effective_weight:.1f}, damped so routers "
            "do not stampede off it together"
        )

    def split(self, use_load: bool) -> dict[str, float]:
        if not self.backends:
            raise Invalid("no backends to split across")
        weights = {
            name: (
                backend.effective_weight
                if use_load
                else backend.static_weight
            )
            for name, backend in self.backends.items()
        }
        total = sum(weights.values())
        if total == 0:
            raise Invalid("every backend is fully loaded")
        return {
            name: weight / total
            for name, weight in weights.items()
        }

    def correction_report(self) -> str:
        static = self.split(use_load=False)
        corrected = self.split(use_load=True)
        lines = ["static split vs load-corrected:"]
        for name in sorted(self.backends):
            lines.append(
                f"  {name}: {static[name]:.0%} -> "
                f"{corrected[name]:.0%}"
            )
        lines.append(
            "the gap is weight sending traffic to a backend "
            "measurement says is full"
        )
        return "\n".join(lines)
