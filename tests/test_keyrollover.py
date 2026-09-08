from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.keyrollover import Rollover


def rollover() -> Rollover:
    return Rollover(ttl=30)


class TestTheSafePath:
    def test_the_full_dance_keeps_the_invariant(self):
        chosen = rollover()
        assert "one ttl (30)" in chosen.pre_publish(now=0)
        assert "no resolver sees unsigned air" in (
            chosen.activate(now=30)
        )
        verdict = chosen.retire(now=60)
        assert "the invariant kept end to end" in verdict
        assert chosen.stage == "old-retired"

    def test_a_zero_ttl_leaves_no_window(self):
        with pytest.raises(Invalid):
            Rollover(ttl=0)


class TestTheRefusalToSkip:
    def test_activation_needs_a_full_ttl(self):
        chosen = rollover()
        chosen.pre_publish(now=0)
        with pytest.raises(Invalid) as caught:
            chosen.activate(now=20)
        assert "failing closed" in str(caught.value)

    def test_retirement_needs_another_full_ttl(self):
        chosen = rollover()
        chosen.pre_publish(now=0)
        chosen.activate(now=30)
        with pytest.raises(Invalid) as caught:
            chosen.retire(now=45)
        assert "strands caches still holding signatures" in str(
            caught.value
        )

    def test_stages_cannot_be_reordered(self):
        chosen = rollover()
        with pytest.raises(Invalid):
            chosen.activate(now=0)
        with pytest.raises(Invalid):
            chosen.retire(now=0)


class TestTheTimeline:
    def test_the_report_states_the_two_ttl_minimum(self):
        report = rollover().timeline_report()
        assert "at least 60 tick(s), two full ttls" in report
        assert "learns the number here instead of from the outage" in (
            report
        )
