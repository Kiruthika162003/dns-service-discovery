from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.glueless import glue_status, validate_delegation


class TestGlueStatus:
    def test_an_in_zone_nameserver_requires_glue(self):
        assert glue_status("ns1.child.example.", "child.example.") == (
            "required"
        )

    def test_an_out_of_zone_nameserver_forbids_glue(self):
        assert glue_status("ns1.provider.net.", "child.example.") == (
            "forbidden"
        )


class TestValidation:
    def test_a_delegation_with_the_needed_glue_is_reachable(self):
        assert (
            validate_delegation(
                ["ns1.child.example.", "ns1.provider.net."],
                "child.example.",
                glue_provided={"ns1.child.example."},
            )
            == "delegation reachable"
        )

    def test_an_out_of_zone_only_delegation_needs_no_glue(self):
        assert (
            validate_delegation(
                ["ns1.provider.net."],
                "child.example.",
                glue_provided=set(),
            )
            == "delegation reachable"
        )

    def test_an_in_zone_server_without_glue_is_lame(self):
        with pytest.raises(Invalid) as caught:
            validate_delegation(
                ["ns1.child.example."],
                "child.example.",
                glue_provided=set(),
            )
        assert "lame delegation" in str(caught.value)

    def test_a_delegation_with_no_nameservers_is_refused(self):
        with pytest.raises(Invalid):
            validate_delegation([], "child.example.", set())
