from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rendezvous import choose, disruption, ranking

NODES = ["node-a", "node-b", "node-c", "node-d"]
KEYS = [f"svc-{i}" for i in range(2000)]


class TestChoice:
    def test_the_choice_is_stable_for_a_key(self):
        assert choose("svc-1", NODES) == choose("svc-1", NODES)

    def test_the_ranking_lists_every_node_once(self):
        order = ranking("svc-1", NODES)
        assert sorted(order) == sorted(NODES)
        assert order[0] == choose("svc-1", NODES)

    def test_an_empty_pool_is_refused(self):
        with pytest.raises(Invalid):
            choose("svc-1", [])


class TestMinimalDisruption:
    def test_removing_one_of_four_moves_about_a_quarter(self):
        fraction = disruption(KEYS, NODES, "node-b")
        assert 0.18 < fraction < 0.32

    def test_survivors_keep_the_keys_that_did_not_prefer_it(self):
        removed = "node-b"
        survivors = [n for n in NODES if n != removed]
        for key in KEYS:
            if choose(key, NODES) != removed:
                assert choose(key, NODES) == choose(key, survivors)

    def test_removing_a_missing_node_is_ill_posed(self):
        with pytest.raises(Invalid):
            disruption(KEYS, NODES, "ghost")

    def test_removing_the_last_node_is_an_outage(self):
        with pytest.raises(Invalid) as caught:
            disruption(KEYS, ["only"], "only")
        assert "that is an outage" in str(caught.value)
