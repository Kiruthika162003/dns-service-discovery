from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.nsec import NsecZone, nsec3_hash, tradeoff_report


def zone() -> NsecZone:
    built = NsecZone()
    for name in ("alpha.", "gamma.", "omega."):
        built.add(name)
    return built


class TestProvingAbsence:
    def test_the_gap_covers_the_missing_name(self):
        verdict = zone().prove_absence("beta.")
        assert "nothing exists between alpha. and gamma." in (
            verdict
        )
        assert "would sort there and does not, proven" in verdict

    def test_the_proof_leaks_the_boundary_names(self):
        verdict = zone().prove_absence("beta.")
        assert "the two boundary names just leaked" in verdict

    def test_a_query_before_the_first_wraps(self):
        verdict = zone().prove_absence("aardvark.")
        assert "between omega. and alpha." in verdict

    def test_proving_a_present_name_is_refused(self):
        with pytest.raises(Invalid) as caught:
            zone().prove_absence("alpha.")
        assert "proves absence, not presence" in str(caught.value)

    def test_an_empty_zone_cannot_prove(self):
        with pytest.raises(Invalid):
            NsecZone().prove_absence("beta.")

    def test_double_adding_a_name_is_refused(self):
        built = zone()
        with pytest.raises(Invalid):
            built.add("alpha.")


class TestTheZoneWalk:
    def test_the_whole_chain_is_enumerable(self):
        assert zone().zone_walk() == ["alpha.", "gamma.", "omega."]


class TestNsec3:
    def test_hashing_is_deterministic(self):
        assert nsec3_hash("alpha.", 5) == nsec3_hash("alpha.", 5)

    def test_iterations_change_the_hash(self):
        assert nsec3_hash("alpha.", 1) != nsec3_hash("alpha.", 2)

    def test_the_tradeoff_report_prices_both_leaks(self):
        report = tradeoff_report(zone(), iterations=10)
        assert "NSEC leaks all 3 name(s) to a zone walk" in report
        assert "NSEC3 leaks 3 hash(es) instead" in report
        assert "11 hash round(s) per query" in report

    def test_an_empty_zone_has_nothing_to_compare(self):
        with pytest.raises(Invalid):
            tradeoff_report(NsecZone(), iterations=1)
