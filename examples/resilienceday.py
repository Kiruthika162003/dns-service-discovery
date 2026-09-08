"""The resilience day: a backend wobbles, and the guards each do their one job.

Run with: python -m examples.resilienceday
"""

from __future__ import annotations

from beacon.bulkhead import Bulkhead
from beacon.circuitbreaker import CircuitBreaker
from beacon.hedging import Hedge
from beacon.loadshed import LoadShedder
from beacon.panicthreshold import PanicPolicy
from beacon.retrybudget import RetryBudget


def morning_the_breaker_opens():
    breaker = CircuitBreaker(threshold=3, cooldown=10)
    for tick in range(3):
        breaker.on_failure(now=tick)
    blocked = not breaker.allow(now=5)
    probe = breaker.allow(now=13)
    print(f"morning  breaker open blocks = {blocked}, probe at cooldown = {probe}")


def midday_the_retry_budget():
    budget = RetryBudget(ratio=0.2, floor=10)
    print(
        f"midday   fixed 3x loads {budget.fixed_count_load(1000, 3)}, "
        f"budget loads {budget.budgeted_load(1000)}"
    )


def afternoon_the_hedge():
    hedge = Hedge(hedge_after_ms=100)
    latencies = [10] * 95 + [500] * 5
    print(
        f"afternoon hedge fires on {hedge.extra_load_fraction(latencies):.0%}, "
        f"tail {hedge.effective_ms(500, 25)}ms"
    )


def evening_the_shedding():
    shedder = LoadShedder(capacity=100)
    order = shedder.shed_order(90)
    print(f"evening  at 90% load the shed order is {order}")


def night_the_bulkhead():
    bulkhead = Bulkhead({"db": 1, "cache": 2})
    bulkhead.acquire("db")
    bulkhead.acquire("cache")
    print(f"night    db saturated, cache still open: {bulkhead.saturated()}")


def dawn_the_panic():
    policy = PanicPolicy(threshold=0.5)
    routed = len(policy.route_pool(["a", "b"], [f"h{i}" for i in range(10)]))
    print(f"dawn     2 of 10 healthy: panic routes to all {routed}")


def main() -> int:
    morning_the_breaker_opens()
    midday_the_retry_budget()
    afternoon_the_hedge()
    evening_the_shedding()
    night_the_bulkhead()
    dawn_the_panic()
    try:
        Bulkhead({"db": 1}).acquire("ghost")
    except Exception as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
