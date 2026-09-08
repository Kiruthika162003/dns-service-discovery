from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ringelection import forward, leader


class TestForward:
    def test_a_larger_incoming_id_is_forwarded(self):
        assert forward(incoming_id=9, own_id=3) == 9

    def test_a_smaller_incoming_id_is_replaced(self):
        assert forward(incoming_id=2, own_id=6) == 6


class TestLeader:
    def test_the_max_id_wins_regardless_of_order(self):
        assert leader([3, 7, 1, 5]) == 7
        assert leader([7, 1, 3, 5]) == 7

    def test_a_single_node_leads_itself(self):
        assert leader([4]) == 4

    def test_duplicate_ids_are_refused(self):
        with pytest.raises(Invalid):
            leader([3, 3, 5])

    def test_an_empty_ring_is_refused(self):
        with pytest.raises(Invalid):
            leader([])
