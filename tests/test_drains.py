from __future__ import annotations

import pytest

from beacon.drains import DrainingInstance, fleet_drain_report
from beacon.errors import Invalid


def draining(connections: int = 3) -> DrainingInstance:
    instance = DrainingInstance(
        instance_id="web-1", open_connections=connections
    )
    instance.begin_drain(now=0)
    return instance


class TestTheTwoSteps:
    def test_the_drain_names_both_halves(self):
        instance = DrainingInstance(
            instance_id="web-1", open_connections=3
        )
        verdict = instance.begin_drain(now=0)
        assert "no new callers" in verdict
        assert "3 existing connection(s) get their grace" in (
            verdict
        )

    def test_impatience_does_not_speed_a_drain(self):
        instance = draining()
        with pytest.raises(Invalid):
            instance.begin_drain(now=5)

    def test_killing_an_undrained_instance_is_the_outage(self):
        instance = DrainingInstance(
            instance_id="web-1", open_connections=3
        )
        allowed, reason = instance.may_kill(now=0)
        assert not allowed
        assert "the outage, not the deploy" in reason


class TestTheCountdown:
    def test_the_clean_drain_reaches_zero(self):
        instance = draining(connections=2)
        instance.connection_closed()
        instance.connection_closed()
        allowed, reason = instance.may_kill(now=10)
        assert allowed
        assert "every connection finished its own way" in reason

    def test_grace_holds_while_connections_live(self):
        instance = draining()
        allowed, reason = instance.may_kill(now=10)
        assert not allowed
        assert "20 tick(s) of grace left" in reason

    def test_the_deadline_severs_and_logs(self):
        instance = draining()
        allowed, reason = instance.may_kill(now=30)
        assert allowed
        assert "deadline severed 3 connection(s)" in reason
        assert "hold the deploy hostage" in reason


class TestTheFleetReport:
    def test_the_habitual_amputator_is_named(self):
        one = draining(connections=4)
        one.may_kill(now=30)
        two = draining(connections=0)
        report = fleet_drain_report([one, two])
        assert "1 clean, 4 connection(s) severed" in report
        assert "amputating on a schedule" in report
        assert "request timeouts" in report

    def test_clean_fleets_report_clean(self):
        one = draining(connections=1)
        one.connection_closed()
        assert "1 clean, 0 connection(s) severed" in (
            fleet_drain_report([one])
        )
