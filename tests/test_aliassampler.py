from __future__ import annotations

from collections import Counter

import pytest

from beacon.aliassampler import Sampler, build, pick
from beacon.errors import Invalid


class TestBuild:
    def test_a_uniform_distribution_keeps_every_column(self):
        probability, alias = build([1, 1, 1, 1])
        # with equal weights every column keeps its own outcome
        assert all(p == 1.0 for p in probability)
        assert len(alias) == 4

    def test_the_tables_have_one_entry_per_outcome(self):
        probability, alias = build([1, 2, 3])
        assert len(probability) == 3
        assert len(alias) == 3


class TestPick:
    def test_a_low_coin_keeps_the_column_and_a_high_coin_falls_through(self):
        probability, alias = build([1, 3])
        # column 0 has probability 0.5 and aliases to column 1
        assert probability[0] == 0.5
        assert pick(probability, alias, 0, 0.1) == 0
        assert pick(probability, alias, 0, 0.9) == alias[0]

    def test_a_full_column_always_keeps_itself(self):
        probability, alias = build([1, 3])
        # column 1 holds probability 1.0, so any coin keeps it
        assert probability[1] == 1.0
        assert pick(probability, alias, 1, 0.99) == 1

    def test_an_out_of_range_column_is_refused(self):
        probability, alias = build([1, 1])
        with pytest.raises(Invalid):
            pick(probability, alias, 5, 0.5)


class TestSampledFrequencies:
    def test_the_empirical_frequencies_track_the_weights(self):
        sampler = Sampler([1, 1, 2, 4], seed=0)
        counts = Counter(sampler.sample_many(80000))
        fraction = [counts[i] / 80000 for i in range(4)]
        # expected 0.125, 0.125, 0.25, 0.5
        assert abs(fraction[0] - 0.125) < 0.02
        assert abs(fraction[2] - 0.25) < 0.02
        assert abs(fraction[3] - 0.5) < 0.02

    def test_a_zero_weight_outcome_is_never_drawn(self):
        sampler = Sampler([0, 1], seed=1)
        assert set(sampler.sample_many(500)) == {1}


class TestRefusals:
    def test_no_weights_is_refused(self):
        with pytest.raises(Invalid):
            build([])

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(Invalid):
            build([1, -1])

    def test_all_zero_weights_are_refused(self):
        with pytest.raises(Invalid):
            build([0, 0])
