from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.weightedrendezvous import (
    choose,
    disruption,
    distribution,
    ranking,
)

KEYS = [f"key-{i}" for i in range(6000)]


class TestChoice:
    def test_the_choice_is_stable(self):
        nodes = {"a": 1.0, "b": 1.0, "c": 1.0}
        assert choose("key-1", nodes) == choose("key-1", nodes)

    def test_the_ranking_lists_every_node(self):
        nodes = {"a": 1.0, "b": 2.0, "c": 3.0}
        assert sorted(ranking("key-1", nodes)) == ["a", "b", "c"]

    def test_a_zero_weight_node_is_refused(self):
        with pytest.raises(Invalid):
            choose("key-1", {"a": 0.0, "b": 1.0})


class TestWeighting:
    def test_a_heavier_node_takes_proportionally_more(self):
        nodes = {"small": 1.0, "big": 3.0}
        counts = distribution(KEYS, nodes)
        ratio = counts["big"] / counts["small"]
        # roughly 3:1, allow sampling slack
        assert 2.3 < ratio < 3.8

    def test_equal_weights_split_evenly(self):
        nodes = {"a": 1.0, "b": 1.0}
        counts = distribution(KEYS, nodes)
        assert abs(counts["a"] - counts["b"]) < len(KEYS) * 0.1


class TestDisruption:
    def test_removing_a_node_moves_a_bounded_share(self):
        nodes = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0}
        fraction = disruption(KEYS, nodes, "b")
        assert 0.15 < fraction < 0.35

    def test_survivors_keep_keys_that_did_not_prefer_the_removed(self):
        nodes = {"a": 1.0, "b": 1.0, "c": 1.0}
        survivors = {"a": 1.0, "c": 1.0}
        for key in KEYS[:500]:
            if choose(key, nodes) != "b":
                assert choose(key, nodes) == choose(key, survivors)
