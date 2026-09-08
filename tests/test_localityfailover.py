from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.localityfailover import (
    failover_breakpoint,
    local_share,
    route,
    spill,
)


class TestLocalShare:
    def test_a_fully_healthy_zone_keeps_everything(self):
        assert local_share(1.0) == 1.0

    def test_a_small_dip_is_absorbed_locally(self):
        # 0.8 * 1.4 = 1.12, capped at 1.0
        assert local_share(0.8) == 1.0

    def test_a_real_loss_caps_below_one(self):
        assert local_share(0.5) == pytest.approx(0.7)

    def test_a_fraction_outside_zero_to_one_is_refused(self):
        with pytest.raises(Invalid):
            local_share(1.5)

    def test_a_factor_below_one_is_refused(self):
        with pytest.raises(Invalid) as caught:
            local_share(1.0, overprovision=0.9)
        assert "reluctance to failover" in str(caught.value)


class TestSpillAndBreakpoint:
    def test_no_spill_above_the_breakpoint(self):
        assert spill(0.8) == 0.0

    def test_spill_appears_below_the_breakpoint(self):
        assert spill(0.5) == pytest.approx(0.3)

    def test_the_breakpoint_is_the_factor_reciprocal(self):
        assert failover_breakpoint(1.4) == pytest.approx(1 / 1.4)


class TestRoute:
    def test_it_reports_full_local_absorption(self):
        assert "no cross-zone spill" in route(0.8)

    def test_it_reports_the_spill(self):
        assert "spills to the next zone" in route(0.5)
