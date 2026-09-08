from __future__ import annotations

from beacon.pncounter import PNCounter


class TestValue:
    def test_increments_and_decrements_net_out(self):
        counter = PNCounter()
        counter.increment("a", 5)
        counter.decrement("a", 2)
        assert counter.value() == 3

    def test_the_value_can_go_negative(self):
        counter = PNCounter()
        counter.decrement("a", 4)
        assert counter.value() == -4


class TestMerge:
    def test_merge_reconciles_both_halves(self):
        left = PNCounter()
        left.increment("a", 3)
        right = PNCounter()
        right.decrement("b", 1)
        merged = left.merge(right)
        assert merged.value() == 2

    def test_merge_is_commutative(self):
        left = PNCounter()
        left.increment("a", 3)
        left.decrement("a", 1)
        right = PNCounter()
        right.increment("b", 2)
        assert left.merge(right).value() == right.merge(left).value()

    def test_a_decrement_survives_a_merge_that_kept_a_bigger_total(
        self,
    ):
        # a decrement on one replica is an increment to the negative
        # half, so a naive keep-the-larger merge cannot erase it
        left = PNCounter()
        left.increment("a", 10)
        right = PNCounter()
        right.increment("a", 10)
        right.decrement("b", 4)
        merged = left.merge(right)
        assert merged.value() == 6
