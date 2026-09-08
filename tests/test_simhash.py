from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.simhash import hamming, near_duplicate, simhash


class TestSimhash:
    def test_identical_features_hash_identically(self):
        features = [f"word{i}" for i in range(50)]
        assert simhash(features) == simhash(list(features))

    def test_an_empty_input_is_refused(self):
        with pytest.raises(Invalid):
            simhash([])


class TestNearDuplicate:
    def test_a_small_change_stays_close(self):
        base = [f"word{i}" for i in range(50)]
        changed = [*base[:-1], "word-different"]
        assert near_duplicate(simhash(base), simhash(changed), threshold=6)

    def test_unrelated_inputs_are_far(self):
        a = simhash([f"alpha{i}" for i in range(50)])
        b = simhash([f"omega{i}" for i in range(50)])
        assert not near_duplicate(a, b, threshold=3)

    def test_a_negative_threshold_is_refused(self):
        with pytest.raises(Invalid):
            near_duplicate(1, 2, threshold=-1)


class TestHamming:
    def test_it_counts_differing_bits(self):
        assert hamming(0b1010, 0b1001) == 2

    def test_equal_values_have_zero_distance(self):
        assert hamming(42, 42) == 0
