from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.gcounter import GCounter


class TestCounting:
    def test_increments_sum_across_replicas(self):
        counter = GCounter()
        counter.increment("a", 3)
        counter.increment("b", 2)
        assert counter.value() == 5

    def test_a_negative_increment_is_refused(self):
        with pytest.raises(Invalid) as caught:
            GCounter().increment("a", -1)
        assert "Use a PN-counter" in str(caught.value)


class TestMerge:
    def test_merge_keeps_every_replicas_progress(self):
        left = GCounter({"a": 3, "b": 1})
        right = GCounter({"a": 1, "b": 5})
        merged = left.merge(right)
        assert merged.value() == 3 + 5

    def test_merge_is_commutative(self):
        left = GCounter({"a": 3})
        right = GCounter({"a": 1, "b": 2})
        assert left.merge(right).counts == right.merge(left).counts

    def test_merge_is_idempotent(self):
        counter = GCounter({"a": 3, "b": 2})
        assert counter.merge(counter).counts == counter.counts

    def test_a_concurrent_increment_is_not_double_counted(self):
        # both start from a shared state then a increments locally
        left = GCounter({"a": 2})
        right = GCounter({"a": 2})
        left.increment("a", 1)
        merged = left.merge(right)
        assert merged.value() == 3
