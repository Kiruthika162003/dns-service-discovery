from __future__ import annotations

from beacon.kahansum import kahan_sum


def _naive_fold(values: list[float]) -> float:
    total = 0.0
    for value in values:
        total = total + value
    return total


class TestKahanSum:
    def test_it_matches_the_exact_sum_of_simple_integers(self):
        assert kahan_sum([1.0, 2.0, 3.0, 4.0]) == 10.0

    def test_the_empty_list_sums_to_zero(self):
        assert kahan_sum([]) == 0.0

    def test_it_keeps_small_terms_a_naive_fold_loses(self):
        # a large accumulator rounds away each small term in a naive fold
        data = [1e16] + [1.0] * 1000
        exact = 1e16 + 1000
        assert _naive_fold(data) != exact  # the naive fold really does lose them
        assert kahan_sum(data) == exact

    def test_it_agrees_with_a_naive_fold_when_magnitudes_are_similar(self):
        data = [0.5, 1.5, 2.5, 3.5]
        assert kahan_sum(data) == _naive_fold(data)
