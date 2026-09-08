from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ttlclamp import CEILING, FLOOR, ClampLedger


class TestClamping:
    def test_the_reasonable_middle_is_trusted_as_written(self):
        ledger = ClampLedger()
        ttl, verdict = ledger.clamp("www.", 300)
        assert ttl == 300
        assert "trusted as written" in verdict

    def test_the_twitchy_ttl_is_floored_with_the_reason(self):
        ledger = ClampLedger()
        ttl, verdict = ledger.clamp("spam.", 1)
        assert ttl == FLOOR
        assert "turns the cache into a relay" in verdict

    def test_immortality_is_ceilinged_with_the_reason(self):
        ledger = ClampLedger()
        ttl, verdict = ledger.clamp("forever.", 604_800)
        assert ttl == CEILING
        assert "cannot be flushed remotely" in verdict

    def test_zero_is_a_statement_not_a_mistake(self):
        ledger = ClampLedger()
        ttl, verdict = ledger.clamp("nocache.", 0)
        assert ttl == 0
        assert "a statement, not a mistake" in verdict

    def test_negative_durations_are_refused(self):
        with pytest.raises(Invalid):
            ClampLedger().clamp("odd.", -1)


class TestTheIndictment:
    def test_the_floor_fleet_indicts_the_upstreams(self):
        ledger = ClampLedger()
        for number in range(3):
            ledger.clamp(f"twitchy-{number}.", 2)
        ledger.clamp("calm.", 300)
        report = ledger.indictment()
        assert "3 floored" in report
        assert "defending its own bill" in report

    def test_the_price_line_is_always_printed(self):
        ledger = ClampLedger()
        ledger.clamp("calm.", 300)
        assert "no clamp is free" in ledger.indictment()

    def test_the_ceiling_fleet_indicts_the_immortal(self):
        ledger = ClampLedger()
        ledger.clamp("forever.", 100_000)
        ledger.clamp("forever2.", 100_000)
        report = ledger.indictment()
        assert "defending its flushability" in report
        assert "27200 tick(s) of staleness risk" in report
