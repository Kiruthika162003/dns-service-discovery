"""Locality failover: keep traffic local until local capacity thins, then spill deliberately.

Routing every request to the nearest zone is right until that
zone loses hosts, at which point sending it all the local traffic
anyway overloads the survivors while a healthy remote zone sits
idle. Locality failover spills the overflow to the next zone, but
naively, spilling the instant a single host goes unhealthy would
send traffic across zones for a dip that the local zone could
easily absorb, trading latency for nothing. The overprovisioning
factor is the fix: the local zone is treated as able to carry its
healthy fraction times the factor, so with a factor of 1.4 a zone
keeps all of its traffic until its healthy fraction falls below
about seventy-one percent, and only then does the remainder spill.
The factor is a deliberate reluctance to failover, absorbing
small dips locally and reserving the cross-zone cost for the real
losses, and the module computes the local share and the spill so
the breakpoint is a number an operator can see rather than a
surprise during an incident.
"""

from __future__ import annotations

from beacon.errors import Invalid


def local_share(
    healthy_fraction: float, overprovision: float = 1.4
) -> float:
    if not 0.0 <= healthy_fraction <= 1.0:
        raise Invalid(
            f"a healthy fraction of {healthy_fraction} is not a "
            "share between zero and one"
        )
    if overprovision < 1.0:
        raise Invalid(
            "an overprovision factor below one would spill even a "
            "fully healthy zone; the factor is a reluctance to "
            "failover, not an eagerness"
        )
    return min(1.0, healthy_fraction * overprovision)


def spill(
    healthy_fraction: float, overprovision: float = 1.4
) -> float:
    return 1.0 - local_share(healthy_fraction, overprovision)


def failover_breakpoint(overprovision: float = 1.4) -> float:
    if overprovision < 1.0:
        raise Invalid("the factor must be at least one to have a breakpoint")
    return 1.0 / overprovision


def route(
    healthy_fraction: float, overprovision: float = 1.4
) -> str:
    kept = local_share(healthy_fraction, overprovision)
    spilled = 1.0 - kept
    if spilled == 0.0:
        return (
            f"{healthy_fraction:.0%} healthy: local absorbs it "
            "all, no cross-zone spill"
        )
    return (
        f"{healthy_fraction:.0%} healthy: local keeps {kept:.0%}, "
        f"{spilled:.0%} spills to the next zone"
    )
