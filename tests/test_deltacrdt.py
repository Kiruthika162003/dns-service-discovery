from __future__ import annotations

from beacon.deltacrdt import DeltaGCounter


class TestDelta:
    def test_increment_returns_only_the_changed_entry(self):
        counter = DeltaGCounter()
        counter.increment("a", 3)
        delta = counter.increment("a", 2)
        assert delta == {"a": 5}

    def test_a_delta_carries_one_replica(self):
        counter = DeltaGCounter({"a": 1, "b": 2})
        delta = counter.increment("b", 1)
        assert delta == {"b": 3}


class TestConvergence:
    def test_applying_a_delta_merges_it(self):
        left = DeltaGCounter()
        right = DeltaGCounter()
        delta = left.increment("a", 4)
        right.merge_delta(delta)
        assert right.value() == 4

    def test_a_delta_is_idempotent(self):
        target = DeltaGCounter()
        delta = {"a": 5}
        target.merge_delta(delta)
        target.merge_delta(delta)  # applied twice
        assert target.value() == 5

    def test_out_of_order_deltas_still_converge(self):
        source = DeltaGCounter()
        d1 = source.increment("a", 1)
        d2 = source.increment("a", 1)  # now {a:2}
        target = DeltaGCounter()
        target.merge_delta(d2)  # newer first
        target.merge_delta(d1)  # older second
        assert target.value() == 2
