from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.zonevalidation import ZoneValidator


def clean() -> ZoneValidator:
    built = ZoneValidator()
    built.define("www.example.com.")
    built.define("ns1.example.com.")
    built.add_ns("eu.example.com.", "ns1.example.com.")
    return built


class TestFatalBreaks:
    def test_a_delegation_into_the_void_is_fatal(self):
        built = ZoneValidator()
        built.add_ns("eu.example.com.", "ns1.nowhere.")
        fatal, _ = built.validate()
        assert any("delegation into the void" in f for f in fatal)

    def test_a_circular_cname_is_fatal(self):
        built = ZoneValidator()
        built.add_cname("a.example.com.", "b.example.com.")
        built.add_cname("b.example.com.", "a.example.com.")
        fatal, _ = built.validate()
        assert any("an alias chain that circles" in f for f in fatal)

    def test_load_refuses_a_fatal_zone(self):
        built = ZoneValidator()
        built.add_ns("eu.example.com.", "ns1.nowhere.")
        with pytest.raises(Invalid) as caught:
            built.load_verdict()
        assert "refusing to load" in str(caught.value)


class TestWarnings:
    def test_a_wildcard_shadowing_explicit_is_a_warning(self):
        built = ZoneValidator()
        built.define("*.dev.example.com.")
        built.define("real.dev.example.com.")
        fatal, warnings = built.validate()
        assert fatal == []
        assert any("shadows explicit" in w for w in warnings)

    def test_a_warned_zone_still_loads(self):
        built = ZoneValidator()
        built.define("*.dev.example.com.")
        built.define("real.dev.example.com.")
        verdict = built.load_verdict()
        assert "loaded with 1 warning(s)" in verdict
        assert "gets disabled" in verdict


class TestCleanLoad:
    def test_a_clean_zone_loads_plainly(self):
        assert clean().load_verdict() == (
            "loaded clean; every relationship resolves"
        )

    def test_a_terminating_cname_is_not_circular(self):
        built = clean()
        built.add_cname("blog.example.com.", "www.example.com.")
        fatal, _ = built.validate()
        assert fatal == []
