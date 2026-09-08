from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.scuttlebutt import deltas_for_peer, keys_i_need, prioritize

MINE = {
    "n1": ("up", 5),
    "n2": ("down", 3),
    "n3": ("up", 9),
}


class TestDeltas:
    def test_only_newer_keys_are_sent(self):
        peer_digest = {"n1": 5, "n2": 1, "n3": 2}
        deltas = deltas_for_peer(MINE, peer_digest)
        assert set(deltas) == {"n2", "n3"}

    def test_a_key_the_peer_lacks_entirely_is_sent(self):
        deltas = deltas_for_peer(MINE, {"n1": 5})
        assert "n2" in deltas and "n3" in deltas


class TestNeeds:
    def test_keys_the_peer_leads_are_requested(self):
        my_digest = {"n1": 5, "n2": 3, "n3": 9}
        peer_digest = {"n1": 8, "n2": 3, "n4": 1}
        assert keys_i_need(my_digest, peer_digest) == ["n1", "n4"]


class TestPriority:
    def test_the_biggest_gap_goes_first(self):
        peer_digest = {"n1": 4, "n2": 0, "n3": 2}
        deltas = deltas_for_peer(MINE, peer_digest)
        # gaps: n1=1, n2=3, n3=7 -> order n3, n2, n1
        assert prioritize(deltas, peer_digest, budget=2) == ["n3", "n2"]

    def test_a_negative_budget_is_refused(self):
        with pytest.raises(Invalid):
            prioritize({}, {}, budget=-1)
