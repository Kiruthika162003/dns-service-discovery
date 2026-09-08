from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.retryafter import response, retry_after


class TestRetryAfter:
    def test_a_full_token_needs_no_wait(self):
        assert retry_after(tokens=1.0, refill_rate=0.5) == 0

    def test_it_computes_the_wait_to_the_next_token(self):
        # 0.5 tokens, refill 0.1/s -> need 0.5 more -> 5s
        assert retry_after(tokens=0.5, refill_rate=0.1) == 5

    def test_it_rounds_up_a_partial_second(self):
        assert retry_after(tokens=0.0, refill_rate=0.3) == 4  # ceil(1/0.3)

    def test_a_nonpositive_rate_is_refused(self):
        with pytest.raises(Invalid):
            retry_after(0.0, 0.0)


class TestResponse:
    def test_an_allowed_request_is_200(self):
        assert response(tokens=2.0, refill_rate=1.0) == (200, 0)

    def test_a_limited_request_is_429_with_a_wait(self):
        status, wait = response(tokens=0.0, refill_rate=0.5)
        assert status == 429
        assert wait == 2
