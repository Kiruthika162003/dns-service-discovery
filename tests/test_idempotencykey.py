from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.idempotencykey import IdempotencyStore


class TestDedup:
    def test_a_first_request_executes(self):
        store = IdempotencyStore(window=100)
        status, result = store.process("k1", now=0, result="charged")
        assert status == "executed"
        assert result == "charged"

    def test_a_retry_within_the_window_returns_the_first_result(self):
        store = IdempotencyStore(window=100)
        store.process("k1", now=0, result="charged")
        status, result = store.process("k1", now=10, result="charged-again")
        assert status == "cached"
        assert result == "charged"  # the first result, not the retry's

    def test_a_different_key_executes_independently(self):
        store = IdempotencyStore(window=100)
        store.process("k1", now=0, result="a")
        status, _ = store.process("k2", now=1, result="b")
        assert status == "executed"


class TestWindow:
    def test_a_retry_after_the_window_re_executes(self):
        store = IdempotencyStore(window=100)
        store.process("k1", now=0, result="first")
        status, result = store.process("k1", now=150, result="second")
        assert status == "executed"
        assert result == "second"

    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            IdempotencyStore(window=0)
