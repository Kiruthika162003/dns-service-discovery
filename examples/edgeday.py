"""An edge day: capacity, anycast, subsets, and the poisoner turned away.

Run with: python -m examples.edgeday
"""

from __future__ import annotations

from beacon.anycast import AnycastFabric
from beacon.bailiwick import BailiwickFilter
from beacon.capacity import CapacityRouter
from beacon.names import Name
from beacon.p2c import assign_blind, assign_two_choice
from beacon.records import Record


def morning_the_capacity():
    router = CapacityRouter()
    router.add("big", 60)
    router.add("small", 40)
    router.report_load("big", 0.9)
    report = router.correction_report()
    print(f"morning: {report.splitlines()[1].strip()}")


def midday_the_anycast():
    fabric = AnycastFabric()
    for site in ("eu", "us", "asia"):
        fabric.add_site(site, 10)
    clients = {
        f"c{number}": (
            "eu" if number < 6 else "us" if number < 10 else "asia"
        )
        for number in range(14)
    }
    for client, site in clients.items():
        fabric.route_client(client, site)
    reroute = {
        client: ("us" if home == "eu" else "eu")
        for client, home in clients.items()
    }
    print(f"midday:  {fabric.surge_report(reroute).split(';')[0]}")


def afternoon_the_balance():
    blind = assign_blind(1000, 10)
    smart = assign_two_choice(1000, 10)
    print(
        f"afternoon: blind spread {blind.spread()}, "
        f"two-choice spread {smart.spread()}"
    )


def evening_the_poisoner():
    guard = BailiwickFilter()
    kept = guard.filter_response(
        Name.parse("example.com"),
        [
            Record(
                name=Name.parse("www.example.com"),
                rtype="A",
                value="192.0.2.1",
                ttl=300,
            ),
            Record(
                name=Name.parse("bank.net"),
                rtype="A",
                value="203.0.113.66",
                ttl=300,
            ),
        ],
        now=5,
    )
    print(
        f"evening: kept {len(kept)}, discarded "
        f"{len(guard.discard_log)} out-of-district"
    )


def main() -> int:
    morning_the_capacity()
    midday_the_anycast()
    afternoon_the_balance()
    evening_the_poisoner()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
