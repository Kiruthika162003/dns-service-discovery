from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.hedging import Hedge


class TestFiring:
    def test_a_fast_primary_never_hedges(self):
        hedge = Hedge(hedge_after_ms=100)
        assert not hedge.fires(80)
        assert hedge.effective_ms(80, 20) == 80

    def test_a_slow_primary_hedges_and_the_backup_can_win(self):
        hedge = Hedge(hedge_after_ms=100)
        assert hedge.fires(900)
        assert hedge.effective_ms(900, 30) == 130

    def test_a_negative_delay_is_refused(self):
        with pytest.raises(Invalid):
            Hedge(hedge_after_ms=-1)


class TestTheLoadIsNotDoubled:
    def test_a_p95_delay_fires_on_about_a_twentieth(self):
        latencies = [10] * 95 + [500] * 5
        hedge = Hedge(hedge_after_ms=100)
        assert hedge.extra_load_fraction(latencies) == 0.05

    def test_the_tail_collapses_to_delay_plus_fast_backup(self):
        hedge = Hedge(hedge_after_ms=100)
        assert hedge.effective_ms(500, 25) == 125

    def test_no_latencies_is_refused(self):
        with pytest.raises(Invalid):
            Hedge(100).extra_load_fraction([])
