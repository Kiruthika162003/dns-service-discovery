"""A discovery day: leases, health, subsets, and the wheel.

Run with: python -m examples.discoveryday
"""

from __future__ import annotations

from beacon.errors import Missing
from beacon.healthchecks import HealthBoard
from beacon.registry import Registry
from beacon.subsetting import SubsetPlan
from beacon.weighting import Endpoint, locality_order, share_report


def morning_the_leases():
    registry = Registry()
    for number in range(1, 4):
        registry.register(
            "billing",
            f"bill-{number}",
            f"10.0.0.{number}",
            8080,
            now=0,
        )
    registry.renew("billing", "bill-1", now=20)
    found = registry.discover("billing", now=35)
    print(
        f"morning: {len(found)} of 3 answer; "
        f"{registry.ghosts_refused} ghost(s) refused"
    )


def midday_the_health():
    board = HealthBoard()
    board.track("bill-1")
    for tick in range(1, 3):
        board.observe("bill-1", False, now=tick)
    verdict = board.observe("bill-1", False, now=3)
    print(f"midday:  {verdict}")


def afternoon_the_subsets():
    plan = SubsetPlan(
        backends=tuple(f"b-{number:02}" for number in range(20)),
        subset_size=4,
    )
    clients = [f"client-{number}" for number in range(50)]
    report = plan.coverage_report(clients)
    print(f"afternoon: {report.splitlines()[0]}")


def evening_the_wheel():
    endpoints = [
        Endpoint(instance_id="big-1", zone="eu-1", weight=3),
        Endpoint(instance_id="small-1", zone="eu-2", weight=1),
    ]
    report = share_report(endpoints, requests=8)
    print(f"evening: {report.splitlines()[1].strip()}")
    _, note = locality_order(
        [Endpoint(instance_id="small-1", zone="eu-2", weight=1)],
        caller_zone="eu-1",
    )
    print(f"night:   {note.split(';')[0]}")


def main() -> int:
    morning_the_leases()
    midday_the_health()
    afternoon_the_subsets()
    evening_the_wheel()
    try:
        Registry().discover("anything", now=0)
    except Missing as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
