from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.forwarders import ForwarderPolicy


class TestForwardOnly:
    def test_the_failure_is_an_honest_refusal(self):
        policy = ForwarderPolicy(mode="forward-only")
        with pytest.raises(Refused) as caught:
            policy.resolve(
                forwarder_up=False,
                forwarder_latency=0,
                direct_latency=20,
            )
        assert "means what it says" in str(caught.value)

    def test_the_verdict_declares_the_total_trust(self):
        policy = ForwarderPolicy(mode="forward-only")
        with pytest.raises(Refused):
            policy.resolve(False, 0, 20)
        verdict = policy.health_verdict()
        assert "1 failure(s) were 1 refusal(s)" in verdict
        assert "total and declared" in verdict


class TestForwardFirst:
    def test_the_fallback_proves_it_opens(self):
        policy = ForwarderPolicy(mode="forward-first")
        verdict = policy.resolve(
            forwarder_up=False,
            forwarder_latency=0,
            direct_latency=25,
        )
        assert "the escape hatch proved it opens" in verdict
        assert policy.fallback_exercises == 1

    def test_the_never_opened_hatch_is_a_painted_handle(self):
        policy = ForwarderPolicy(mode="forward-first")
        for _ in range(10):
            policy.resolve(True, 15, 20)
        verdict = policy.health_verdict()
        assert "never once run" in verdict
        assert "a wall with a handle painted on" in verdict

    def test_the_slow_success_never_triggers_the_fallback(self):
        policy = ForwarderPolicy(mode="forward-first")
        policy.resolve(
            forwarder_up=True,
            forwarder_latency=90,
            direct_latency=20,
        )
        assert policy.fallback_exercises == 0
        assert policy.hostage_ticks == 70

    def test_the_exercised_hatch_reports_the_hostage_bill(self):
        policy = ForwarderPolicy(mode="forward-first")
        policy.resolve(True, 90, 20)
        policy.resolve(False, 0, 25)
        verdict = policy.health_verdict()
        assert "fallback exercised 1 time(s)" in verdict
        assert "70 tick(s) spent hostage" in verdict


class TestModes:
    def test_an_unknown_mode_is_refused(self):
        with pytest.raises(Invalid):
            ForwarderPolicy(mode="forward-maybe")
