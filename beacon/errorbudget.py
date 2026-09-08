"""Error budgets: turn an SLO into a spendable quantity, and alert on how fast it is burning.

A service-level objective like three-nines availability is not a
promise of perfection but a permission to fail a little, and the
error budget makes that permission concrete: over the window, the
number of failures the objective tolerates is a budget, and every
error spends from it. Framed this way, reliability stops being a
vague aspiration and becomes an account an operator manages, with
room to spend on risky deploys while the budget is healthy and a
reason to freeze changes when it is nearly gone. The burn rate is the
part that catches trouble early. It is the ratio of the current error
rate to the rate the budget could sustain across the whole window, so
a burn rate of one exhausts the budget exactly at the window's end
while a burn rate of many times that would exhaust it in a fraction
of the window, and alerting on a high burn rate fires while there is
still budget left to protect rather than after the objective is
already missed. The module computes the budget from the objective and
the window, the remaining budget after some errors, and the burn
rate, and decides whether the burn is fast enough to alert, so an SLO
becomes a managed quantity rather than a number checked after the
fact.
"""

from __future__ import annotations

from beacon.errors import Invalid


class ErrorBudget:
    def __init__(self, objective: float, window_requests: int) -> None:
        if not 0.0 < objective < 1.0:
            raise Invalid(
                f"an objective of {objective} must be a success "
                "fraction strictly between zero and one"
            )
        if window_requests < 1:
            raise Invalid("a window of zero requests has no budget")
        self.objective = objective
        self.window_requests = window_requests

    def budget(self) -> float:
        return (1.0 - self.objective) * self.window_requests

    def remaining(self, errors: int) -> float:
        return self.budget() - errors

    def burn_rate(self, error_fraction: float) -> float:
        if error_fraction < 0:
            raise Invalid("an error fraction is never negative")
        return error_fraction / (1.0 - self.objective)

    def is_fast_burn(
        self, error_fraction: float, threshold: float = 14.4
    ) -> bool:
        return self.burn_rate(error_fraction) >= threshold
