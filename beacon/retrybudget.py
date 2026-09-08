"""A retry budget: invisible while the backend is healthy, decisive when it is drowning.

Retries are a cure that becomes the disease. A backend slows,
clients time out and retry, and the retries pile onto the very
backend that was already struggling, so a small wobble becomes a
retry storm that turns three-times-normal load onto a service at
its weakest. A fixed retry count, try three times always, is the
trap: it multiplies load exactly when load is the problem. A
retry budget instead caps retries as a fraction of successful
traffic, a small floor plus a ratio of the request rate, and
refuses a retry once the budget is spent. The behavior is worth
stating plainly because it surprises people who expect a budget
to be a constant nuisance: while the backend is healthy almost
nothing fails, so retries stay far under the budget and the cap
never bites, and only when failures spike does the budget engage
and cap the added load, so the budget is invisible in health and
decisive in failure, which is exactly backwards from the fixed
count that is generous in health and lethal in failure.
"""

from __future__ import annotations

from beacon.errors import Invalid


class RetryBudget:
    def __init__(self, ratio: float = 0.2, floor: int = 10) -> None:
        if ratio < 0:
            raise Invalid(
                "a negative retry ratio would forbid retries and "
                "then owe them back; a budget is a cap, not a debt"
            )
        self.ratio = ratio
        self.floor = floor

    def allowance(self, requests: int) -> int:
        return self.floor + int(self.ratio * requests)

    def may_retry(self, requests: int, retries_spent: int) -> bool:
        return retries_spent < self.allowance(requests)

    def fixed_count_load(self, requests: int, attempts: int) -> int:
        return requests * attempts

    def budgeted_load(self, requests: int) -> int:
        return requests + self.allowance(requests)

    def storm_delta(self, requests: int, attempts: int) -> int:
        return self.fixed_count_load(
            requests, attempts
        ) - self.budgeted_load(requests)
