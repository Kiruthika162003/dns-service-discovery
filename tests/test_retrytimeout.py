from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.retrytimeout import attempts_allowed, should_attempt


class TestAttemptsAllowed:
    def test_the_count_binds_when_time_is_ample(self):
        # 5s deadline, 1s attempts, 2 retries -> count binds at 3
        assert attempts_allowed(per_attempt=1, total_deadline=5, max_retries=2) == 3

    def test_the_deadline_binds_when_attempts_are_slow(self):
        # 5s deadline, 2s attempts, 10 retries -> time binds at 2
        assert attempts_allowed(per_attempt=2, total_deadline=5, max_retries=10) == 2

    def test_a_nonpositive_duration_is_refused(self):
        with pytest.raises(Invalid):
            attempts_allowed(0, 5, 2)


class TestShouldAttempt:
    def test_it_attempts_within_both_limits(self):
        assert should_attempt(
            attempt=1, elapsed=1, per_attempt=2, total_deadline=5, max_retries=3
        )

    def test_it_refuses_when_the_count_is_spent(self):
        assert not should_attempt(
            attempt=4, elapsed=0, per_attempt=1, total_deadline=100, max_retries=3
        )

    def test_it_refuses_when_no_time_for_a_full_attempt(self):
        # elapsed 4, attempt takes 2, deadline 5 -> 6 > 5, no time
        assert not should_attempt(
            attempt=1, elapsed=4, per_attempt=2, total_deadline=5, max_retries=3
        )
