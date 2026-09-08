from __future__ import annotations

import pytest

from beacon.errors import Missing
from beacon.zonecut import encloses, zone_cut

APEXES = {"example.", "sub.example.", "com."}


class TestEncloses:
    def test_an_apex_encloses_its_descendant(self):
        assert encloses("example.", "www.example.")

    def test_an_apex_encloses_itself(self):
        assert encloses("example.", "example.")

    def test_an_unrelated_name_is_not_enclosed(self):
        assert not encloses("example.", "other.net.")


class TestZoneCut:
    def test_the_deepest_enclosing_apex_wins(self):
        assert zone_cut("host.sub.example.", APEXES) == "sub.example."

    def test_a_name_above_the_delegation_uses_the_parent(self):
        assert zone_cut("www.example.", APEXES) == "example."

    def test_a_name_with_no_enclosing_zone_is_missing(self):
        with pytest.raises(Missing) as caught:
            zone_cut("host.elsewhere.org.", APEXES)
        assert "must refer or recurse" in str(caught.value)
