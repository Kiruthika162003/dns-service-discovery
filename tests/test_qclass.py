from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.qclass import code_of, handle


class TestHandling:
    def test_a_matching_class_is_answered(self):
        assert handle("IN", zone_class="IN") == "answer"

    def test_any_is_a_meta_query(self):
        assert handle("ANY", zone_class="IN") == "meta-query across classes"

    def test_a_mismatched_class_is_refused(self):
        with pytest.raises(Refused) as caught:
            handle("HS", zone_class="IN")
        assert "invent an authority" in str(caught.value)

    def test_an_unknown_class_is_refused(self):
        with pytest.raises(Invalid):
            handle("XX", zone_class="IN")


class TestCodes:
    def test_known_classes_have_numbers(self):
        assert code_of("IN") == 1
        assert code_of("ANY") == 255

    def test_an_unknown_class_has_no_number(self):
        with pytest.raises(Invalid):
            code_of("ZZ")
