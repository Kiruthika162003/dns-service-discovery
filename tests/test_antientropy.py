from __future__ import annotations

import pytest

from beacon.antientropy import MemberCatalog, sync_round
from beacon.errors import Invalid


def pair() -> tuple[MemberCatalog, MemberCatalog]:
    left = MemberCatalog(name="node-a")
    right = MemberCatalog(name="node-b")
    for member in (left, right):
        member.put("billing/b1", "10.0.0.1:80", version=5)
        member.put("search/s1", "10.0.0.2:80", version=8)
    return left, right


class TestAgreement:
    def test_agreement_costs_one_hash_compare(self):
        left, right = pair()
        verdict = sync_round(left, right, now=100)
        assert "no keys exchanged" in verdict
        assert "the common case doing its job" in verdict


class TestRepair:
    def test_the_higher_version_wins_either_direction(self):
        left, right = pair()
        left.put("billing/b1", "10.0.0.9:80", version=12)
        right.put("search/s1", "10.0.0.7:80", version=11)
        verdict = sync_round(left, right, now=20)
        assert "2 drifted key(s) repaired by version" in verdict
        assert left.state["search/s1"] == ("10.0.0.7:80", 11)
        assert right.state["billing/b1"] == ("10.0.0.9:80", 12)

    def test_a_missing_key_is_drift_too(self):
        left, right = pair()
        left.put("cache/c1", "10.0.0.5:11211", version=9)
        sync_round(left, right, now=15)
        assert right.state["cache/c1"] == (
            "10.0.0.5:11211",
            9,
        )

    def test_the_age_of_the_trust_problem_is_named(self):
        left, right = pair()
        left.put("billing/b1", "10.0.0.9:80", version=12)
        verdict = sync_round(left, right, now=40)
        assert "could have been wrong for up to 35 tick(s)" in (
            verdict
        )

    def test_freshness_is_evidence_popularity_is_not(self):
        left, right = pair()
        left.put("billing/b1", "10.0.0.9:80", version=12)
        verdict = sync_round(left, right, now=20)
        assert "never by majority" in verdict


class TestVersionDiscipline:
    def test_time_does_not_run_backward(self):
        member = MemberCatalog(name="node-a")
        member.put("k", "v", version=5)
        with pytest.raises(Invalid) as caught:
            member.put("k", "v2", version=5)
        assert "time does not run backward" in str(caught.value)
