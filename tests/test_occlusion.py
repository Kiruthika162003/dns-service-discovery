from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.occlusion import is_occluded, occluded_names, report

POINT = "sub.example."
GLUE = {"ns1.sub.example."}


class TestOcclusion:
    def test_a_name_below_the_cut_is_occluded(self):
        assert is_occluded("host.sub.example.", POINT, GLUE)

    def test_permitted_glue_survives(self):
        assert not is_occluded("ns1.sub.example.", POINT, GLUE)

    def test_the_delegation_point_itself_is_not_occluded(self):
        assert not is_occluded("sub.example.", POINT, GLUE)

    def test_a_name_elsewhere_is_untouched(self):
        assert not is_occluded("www.example.", POINT, GLUE)


class TestReporting:
    def test_the_occluded_list_excludes_glue(self):
        names = {
            "host.sub.example.",
            "ns1.sub.example.",
            "deep.host.sub.example.",
            "www.example.",
        }
        hidden = occluded_names(names, POINT, GLUE)
        assert hidden == [
            "deep.host.sub.example.",
            "host.sub.example.",
        ]

    def test_the_report_counts_hidden_and_glue(self):
        names = {"host.sub.example.", "ns1.sub.example."}
        line = report(names, POINT, GLUE)
        assert "1 name(s) occluded" in line
        assert "1 kept as permitted" in line


class TestRefusals:
    def test_out_of_zone_glue_is_a_separate_mistake(self):
        with pytest.raises(Invalid) as caught:
            occluded_names(
                {"host.sub.example."}, POINT, {"ns.elsewhere."}
            )
        assert "lies outside it" in str(caught.value)
