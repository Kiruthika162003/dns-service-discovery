from __future__ import annotations

import pytest

from beacon.emptynonterminal import classify, implied_names
from beacon.errors import Invalid, Missing

APEX = "example."
OWNERS = {"x.a.b.example.", "www.example."}
RECORDS = {
    ("x.a.b.example.", "A"): ["192.0.2.1"],
    ("www.example.", "A"): ["192.0.2.9"],
}


class TestImpliedNames:
    def test_every_ancestor_of_a_child_is_implied(self):
        names = implied_names(OWNERS, APEX)
        assert "a.b.example." in names
        assert "b.example." in names
        assert "example." in names

    def test_a_name_outside_the_zone_is_refused(self):
        with pytest.raises(Invalid) as caught:
            implied_names({"host.other."}, APEX)
        assert "not within the zone" in str(caught.value)


class TestClassification:
    def test_a_direct_hit_is_an_answer(self):
        assert (
            classify("www.example.", "A", RECORDS, OWNERS, APEX)
            == "answer"
        )

    def test_an_empty_non_terminal_is_nodata(self):
        assert (
            classify("a.b.example.", "A", RECORDS, OWNERS, APEX)
            == "nodata"
        )

    def test_a_wrong_type_at_a_real_name_is_nodata(self):
        assert (
            classify("www.example.", "MX", RECORDS, OWNERS, APEX)
            == "nodata"
        )

    def test_a_truly_absent_name_is_nxdomain(self):
        with pytest.raises(Missing) as caught:
            classify("ghost.example.", "A", RECORDS, OWNERS, APEX)
        assert "NXDOMAIN, not the NODATA" in str(caught.value)
