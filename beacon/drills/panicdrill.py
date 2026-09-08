"""Panic mode's reversal: the balancer routes to more hosts exactly as more of them fail.

The drill pins the counterintuitive turn. With eight of ten hosts
healthy the balancer filters normally and routes only to the
eight, but with two of ten healthy it crosses the panic threshold
and routes to all ten, unhealthy included, because concentrating
the load on two survivors would finish them off. The two pools it
returns, eight in the calm case and ten in the panic case, are
the whole point held as numbers: the size of the routed pool
grows as health collapses, which is backwards from every intuition
about filtering and exactly what keeps the survivors alive.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.panicthreshold import PanicPolicy

HOSTS = [f"h{i}" for i in range(10)]


def run() -> Finding:
    policy = PanicPolicy(threshold=0.5)
    calm_pool = policy.route_pool(HOSTS[:8], HOSTS)
    panic_pool = policy.route_pool(HOSTS[:2], HOSTS)
    numbers = {
        "calm_healthy": 8,
        "calm_routed": len(calm_pool),
        "panic_healthy": 2,
        "panic_routed": len(panic_pool),
        "pool_grows_as_health_falls": len(panic_pool)
        > len(calm_pool),
    }
    holds = (
        len(calm_pool) == 8
        and len(panic_pool) == 10
        and numbers["pool_grows_as_health_falls"]
    )
    return Finding(
        drill="panic",
        claim=(
            "at 8/10 healthy the balancer routes to 8, and at "
            "2/10 healthy it routes to all 10, so the routed pool "
            "grows as health collapses to keep the survivors from "
            "being finished off"
        ),
        numbers=numbers,
        holds=holds,
    )
