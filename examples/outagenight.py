"""The outage night: stale beats silent, floors hold, and the registry doubts.

Run with: python -m examples.outagenight
"""

from __future__ import annotations

from beacon.clientcache import ClientCache
from beacon.disobedience import PopulationMix
from beacon.multisite import SitePair
from beacon.selfpreserve import SelfPreservingRegistry
from beacon.servestale import StaleServer


def one_am_the_failover():
    pair = SitePair(primary="eu-west", backup="us-east")
    print(f"01:00  {pair.observe(primary_healthy=False, now=60)}")
    mix = PopulationMix(obedient=80, pinned=20, ttl=60)
    print(
        f"       dead address at +30: "
        f"{mix.traffic_at_dead_address(30)} client(s); at "
        f"+120: {mix.traffic_at_dead_address(120)}, the floor"
    )


def two_am_the_stale_answers():
    stale = StaleServer()
    stale.retire("api.shop.example.", "192.0.2.20", expired_at=100)
    served = stale.serve_stale(
        "api.shop.example.", now=160, live_failed=True
    )
    print(f"02:00  {served.split(':')[0]}")
    print(f"       {stale.outage_ledger().split(';')[0]}")


def three_am_the_client_cache():
    cache = ClientCache()
    cache.store("billing", ("10.0.0.1:80",), now=0)
    print(f"03:00  {cache.serve('billing', now=100)}")
    cache.registry_failed(now=100)
    cache.registry_failed(now=101)
    cache.may_query_registry(now=102)
    print(f"       {cache.politeness_ledger().split(';')[0]}")


def four_am_the_registry_doubts():
    registry = SelfPreservingRegistry(registered=100)
    verdict = registry.observe_window(
        renewals_seen=55, lapsed=45, now=240
    )
    print(f"04:00  {verdict.split(';')[0]}")


def five_am_the_recovery():
    pair = SitePair(primary="eu-west", backup="us-east")
    pair.observe(primary_healthy=False, now=60)
    pair.observe(primary_healthy=True, now=70)
    print(f"05:00  {pair.observe(primary_healthy=True, now=95).split(';')[0]}")


def main() -> int:
    one_am_the_failover()
    two_am_the_stale_answers()
    three_am_the_client_cache()
    four_am_the_registry_doubts()
    five_am_the_recovery()
    try:
        StaleServer().serve_stale("gone.", now=0, live_failed=True)
    except Exception as refusal:
        print(f"honest: {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
