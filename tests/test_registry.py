from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.registry import Registry


def registry() -> Registry:
    built = Registry()
    built.register(
        "billing", "bill-1", "10.0.0.5", 8080, now=0
    )
    built.register(
        "billing", "bill-2", "10.0.0.6", 8080, now=0
    )
    return built


class TestLeases:
    def test_registration_is_a_promise_with_a_deadline(self):
        verdict = Registry().register(
            "api", "api-1", "10.0.0.9", 80, now=100
        )
        assert "vouched for until 130" in verdict
        assert "renew or the vouching stops" in verdict

    def test_renewal_extends_the_vouching(self):
        chosen = registry()
        assert chosen.renew("billing", "bill-1", now=20) == (
            "bill-1 renewed until 50"
        )

    def test_a_lapsed_instance_reregisters_not_renews(self):
        chosen = registry()
        with pytest.raises(Missing) as caught:
            chosen.renew("billing", "bill-1", now=30)
        assert "the interval nobody vouched for" in str(
            caught.value
        )

    def test_a_subtick_lease_expires_before_it_lands(self):
        with pytest.raises(Invalid):
            Registry().register(
                "api", "a", "10.0.0.1", 80, now=0, lease=0
            )


class TestDiscovery:
    def test_only_leased_passing_instances_answer(self):
        chosen = registry()
        found = chosen.discover("billing", now=10)
        assert [i.instance_id for i in found] == [
            "bill-1", "bill-2",
        ]

    def test_the_ghost_is_refused_and_counted(self):
        chosen = registry()
        chosen.renew("billing", "bill-2", now=20)
        found = chosen.discover("billing", now=35)
        assert [i.instance_id for i in found] == ["bill-2"]
        assert chosen.ghosts_refused == 1

    def test_the_failing_instance_is_invisible_to_callers(self):
        chosen = registry()
        chosen.report_health("billing", "bill-1", passing=False)
        found = chosen.discover("billing", now=10)
        assert [i.instance_id for i in found] == ["bill-2"]

    def test_the_sick_stay_registered_for_the_operator(self):
        chosen = registry()
        verdict = chosen.report_health(
            "billing", "bill-1", passing=False
        )
        assert "visible to operators and invisible to callers" in (
            verdict
        )
        assert "bill-1" in chosen.services["billing"]

    def test_a_never_registered_service_is_named_plainly(self):
        with pytest.raises(Missing) as caught:
            registry().discover("bilLing-typo", now=0)
        assert "beats one that looks like a typo" in str(
            caught.value
        )

    def test_nobody_fit_to_answer_is_its_own_message(self):
        chosen = registry()
        chosen.report_health("billing", "bill-1", passing=False)
        chosen.report_health("billing", "bill-2", passing=False)
        with pytest.raises(Missing) as caught:
            chosen.discover("billing", now=10)
        assert "nobody fit to answer" in str(caught.value)


class TestTheCensus:
    def test_the_census_splits_the_three_states(self):
        chosen = registry()
        chosen.report_health("billing", "bill-1", passing=False)
        chosen.discover("billing", now=10)
        census = chosen.census("billing", now=40)
        assert census.startswith(
            "billing: 0 leased (0 failing), 2 lapsed"
        )
