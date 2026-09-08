from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.retrybudget import RetryBudget


class TestAllowance:
    def test_the_allowance_is_a_floor_plus_a_ratio(self):
        budget = RetryBudget(ratio=0.2, floor=10)
        assert budget.allowance(1000) == 10 + 200

    def test_a_negative_ratio_is_refused(self):
        with pytest.raises(Invalid) as caught:
            RetryBudget(ratio=-0.1)
        assert "a cap, not a debt" in str(caught.value)


class TestInvisibleInHealth:
    def test_a_healthy_backend_never_spends_the_budget(self):
        budget = RetryBudget(ratio=0.2, floor=10)
        few_failures = 5
        assert budget.may_retry(1000, few_failures)

    def test_the_budget_bites_only_in_a_storm(self):
        budget = RetryBudget(ratio=0.2, floor=10)
        assert budget.may_retry(1000, 209)
        assert not budget.may_retry(1000, 210)


class TestTheStormItAverts:
    def test_the_fixed_count_triples_load_the_budget_does_not(self):
        budget = RetryBudget(ratio=0.2, floor=10)
        assert budget.fixed_count_load(1000, 3) == 3000
        assert budget.budgeted_load(1000) == 1210

    def test_the_storm_delta_is_the_load_the_budget_removes(self):
        budget = RetryBudget(ratio=0.2, floor=10)
        assert budget.storm_delta(1000, 3) == 3000 - 1210
