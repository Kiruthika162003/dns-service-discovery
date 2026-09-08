from __future__ import annotations

from math import ceil

import pytest

from beacon.boundedload import (
    bounded_assign,
    max_load,
    plain_assign,
)
from beacon.errors import Invalid

NODES = [f"n{i}" for i in range(8)]
KEYS = [f"k{i}" for i in range(1000)]


class TestTheCap:
    def test_no_node_exceeds_the_capacity(self):
        assignment = bounded_assign(KEYS, NODES, spread=1.25)
        cap = ceil(1.25 * len(KEYS) / len(NODES))
        assert max_load(assignment) <= cap

    def test_the_bounded_tail_is_no_worse_than_plain(self):
        bounded = max_load(bounded_assign(KEYS, NODES, 1.25))
        plain = max_load(plain_assign(KEYS, NODES))
        assert bounded <= plain

    def test_every_key_is_placed(self):
        assignment = bounded_assign(KEYS, NODES, spread=1.25)
        assert len(assignment) == len(KEYS)


class TestRefusals:
    def test_a_spread_of_one_is_refused(self):
        with pytest.raises(Invalid) as caught:
            bounded_assign(KEYS, NODES, spread=1.0)
        assert "no room above the average" in str(caught.value)

    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            bounded_assign(KEYS, [], spread=1.25)


class TestTheTradeIsDisplacementForTail:
    def test_a_majority_still_keep_their_first_choice(self):
        plain = plain_assign(KEYS, NODES)
        bounded = bounded_assign(KEYS, NODES, spread=1.25)
        kept = sum(
            1 for key in KEYS if plain[key] == bounded[key]
        )
        assert kept > len(KEYS) * 0.5

    def test_the_displaced_keys_are_the_price_of_the_capped_tail(
        self,
    ):
        plain = plain_assign(KEYS, NODES)
        bounded = bounded_assign(KEYS, NODES, spread=1.25)
        moved = sum(
            1 for key in KEYS if plain[key] != bounded[key]
        )
        tail_cut = max_load(plain) - max_load(bounded)
        assert moved > 0
        assert tail_cut > 0
