from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rrlslip import ResponseRateLimiter


class TestConstruction:
    def test_a_zero_slip_is_refused(self):
        with pytest.raises(Invalid) as caught:
            ResponseRateLimiter(limit=5, slip=0)
        assert "no path\nthrough" in caught.value.args[0] or (
            "no path through" in str(caught.value)
        )

    def test_a_zero_limit_is_refused(self):
        with pytest.raises(Invalid):
            ResponseRateLimiter(limit=0, slip=2)


class TestHandling:
    def test_it_answers_up_to_the_limit(self):
        rrl = ResponseRateLimiter(limit=3, slip=2)
        assert [rrl.handle("v") for _ in range(3)] == [
            "answer",
            "answer",
            "answer",
        ]

    def test_it_slips_a_truncated_response_periodically(self):
        rrl = ResponseRateLimiter(limit=2, slip=2)
        for _ in range(2):
            rrl.handle("v")  # answers
        # over the limit: 1st over -> dropped, 2nd over -> truncated
        assert rrl.handle("v") == "dropped"
        assert rrl.handle("v") == "truncated"

    def test_keys_are_counted_independently(self):
        rrl = ResponseRateLimiter(limit=1, slip=2)
        assert rrl.handle("a") == "answer"
        assert rrl.handle("b") == "answer"
