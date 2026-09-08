from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.failoverguard import should_promote


class TestNoPromotion:
    def test_a_healthy_active_is_not_replaced(self):
        assert not should_promote(
            active_healthy=True,
            witness_reachable=True,
            witness_confirms_dead=False,
        )

    def test_a_witness_that_says_alive_blocks_promotion(self):
        assert not should_promote(
            active_healthy=False,
            witness_reachable=True,
            witness_confirms_dead=False,
        )


class TestPromotion:
    def test_a_confirmed_dead_active_is_replaced(self):
        assert should_promote(
            active_healthy=False,
            witness_reachable=True,
            witness_confirms_dead=True,
        )


class TestAmbiguity:
    def test_an_unreachable_witness_refuses_to_promote(self):
        with pytest.raises(Refused) as caught:
            should_promote(
                active_healthy=False,
                witness_reachable=False,
                witness_confirms_dead=False,
            )
        assert "how split brain happens" in str(caught.value)
