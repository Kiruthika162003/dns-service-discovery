from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.selfpreserve import SelfPreservingRegistry


def registry() -> SelfPreservingRegistry:
    return SelfPreservingRegistry(registered=100)


class TestTheTrigger:
    def test_a_normal_window_evicts_individually(self):
        chosen = registry()
        verdict = chosen.observe_window(
            renewals_seen=97, lapsed=3, now=0
        )
        assert verdict.startswith("normal:")
        assert chosen.may_evict()

    def test_the_mass_lapse_flips_the_suspicion_inward(self):
        chosen = registry()
        verdict = chosen.observe_window(
            renewals_seen=60, lapsed=40, now=0
        )
        assert verdict.startswith("PRESERVING: 60")
        assert "suspects its own hearing" in verdict
        assert not chosen.may_evict()
        assert chosen.evictions_suppressed == 40

    def test_the_floor_is_computed_not_configured(self):
        chosen = registry()
        chosen.observe_window(renewals_seen=84, lapsed=16, now=0)
        assert chosen.preserving
        calm = registry()
        calm.observe_window(renewals_seen=85, lapsed=15, now=0)
        assert not calm.preserving


class TestTheExit:
    def test_recovery_is_by_evidence(self):
        chosen = registry()
        chosen.observe_window(renewals_seen=50, lapsed=50, now=0)
        verdict = chosen.observe_window(
            renewals_seen=92, lapsed=2, now=10
        )
        assert verdict.startswith("recovered:")
        assert "a lie with a clock face" in verdict
        assert chosen.may_evict()

    def test_the_partition_does_not_promise_to_be_short(self):
        chosen = registry()
        for window in range(5):
            chosen.observe_window(
                renewals_seen=40, lapsed=60, now=window
            )
        assert chosen.preserving
        assert chosen.evictions_suppressed == 300


class TestTheNote:
    def test_the_quiet_window_says_leases_told_the_truth(self):
        assert "leases told the truth" in (
            registry().incident_note()
        )

    def test_the_note_names_the_amputation_avoided(self):
        chosen = registry()
        chosen.observe_window(renewals_seen=60, lapsed=40, now=7)
        note = chosen.incident_note()
        assert "1 preservation episode(s), 40 eviction(s)" in note
        assert "[7] entered: 60 of 100" in note
        assert "would have amputated" in note

    def test_an_empty_registry_is_refused(self):
        with pytest.raises(Invalid):
            SelfPreservingRegistry(registered=0)
