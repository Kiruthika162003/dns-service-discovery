from __future__ import annotations

import pytest

from beacon.errorbudget import ErrorBudget
from beacon.errors import Invalid


class TestConstruction:
    def test_an_objective_outside_zero_to_one_is_refused(self):
        with pytest.raises(Invalid):
            ErrorBudget(objective=1.0, window_requests=1000)

    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            ErrorBudget(objective=0.999, window_requests=0)


class TestBudget:
    def test_the_budget_is_the_tolerated_failures(self):
        budget = ErrorBudget(objective=0.99, window_requests=10000)
        assert budget.budget() == pytest.approx(100)

    def test_remaining_subtracts_the_errors(self):
        budget = ErrorBudget(objective=0.99, window_requests=10000)
        assert budget.remaining(errors=30) == pytest.approx(70)


class TestBurnRate:
    def test_a_burn_rate_of_one_matches_the_slo(self):
        budget = ErrorBudget(objective=0.99, window_requests=10000)
        # error fraction equal to (1-slo)=0.01 -> burn rate 1
        assert budget.burn_rate(0.01) == pytest.approx(1.0)

    def test_a_fast_burn_alerts(self):
        budget = ErrorBudget(objective=0.999, window_requests=1000000)
        # 0.015 fraction over a 0.001 budget -> burn rate 15
        assert budget.is_fast_burn(0.015, threshold=14.4)

    def test_a_slow_burn_does_not_alert(self):
        budget = ErrorBudget(objective=0.999, window_requests=1000000)
        assert not budget.is_fast_burn(0.002, threshold=14.4)
