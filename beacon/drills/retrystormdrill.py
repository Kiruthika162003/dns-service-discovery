"""The retry storm the budget averts, priced against the fixed count that causes it.

The fixed retry count and the retry budget diverge exactly when
it matters, under load, and the drill puts the two loads side by
side on the same thousand-request second. A fixed three attempts
turns a thousand requests into three thousand against a backend
that is already struggling, while a budget of a ten-request floor
plus a fifth of the traffic caps the added load at two hundred
ten, for twelve hundred ten total. The drill holds the difference,
seventeen hundred ninety requests of pure amplification the budget
removes, because the number is the whole argument: the fixed count
is generous when the backend is fine and lethal when it is not,
and the budget is the reverse.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.retrybudget import RetryBudget


def run() -> Finding:
    budget = RetryBudget(ratio=0.2, floor=10)
    requests = 1000
    fixed = budget.fixed_count_load(requests, 3)
    budgeted = budget.budgeted_load(requests)
    delta = budget.storm_delta(requests, 3)
    numbers = {
        "fixed_count_load": fixed,
        "budgeted_load": budgeted,
        "amplification_removed": delta,
        "healthy_never_bites": budget.may_retry(requests, 5),
        "storm_is_capped": not budget.may_retry(requests, 210),
    }
    holds = (
        fixed == 3000
        and budgeted == 1210
        and delta == 1790
        and numbers["healthy_never_bites"]
        and numbers["storm_is_capped"]
    )
    return Finding(
        drill="retrystorm",
        claim=(
            "on 1000 requests a fixed three attempts loads 3000 "
            "while a floor-plus-fifth budget loads 1210, removing "
            "1790 requests of amplification, and the cap bites "
            "only in the storm, never in health"
        ),
        numbers=numbers,
        holds=holds,
    )
