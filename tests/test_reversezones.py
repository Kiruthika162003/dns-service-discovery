from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.reversezones import ReverseSynthesizer, reverse_name


def synthesizer() -> ReverseSynthesizer:
    built = ReverseSynthesizer()
    built.add_forward("www.example.com.", "192.0.2.10")
    built.add_forward("api.example.com.", "192.0.2.20")
    return built


class TestSpelling:
    def test_the_address_is_spelled_octet_reversed(self):
        assert reverse_name("192.0.2.10") == (
            "10.2.0.192.in-addr.arpa."
        )

    def test_a_non_quad_has_no_floor(self):
        with pytest.raises(Invalid):
            reverse_name("192.0.2")


class TestSynthesis:
    def test_agreement_by_construction(self):
        zone = synthesizer().synthesize()
        assert zone["10.2.0.192.in-addr.arpa."] == (
            "www.example.com."
        )

    def test_shared_addresses_demand_a_choice(self):
        built = synthesizer()
        built.add_forward("blog.example.com.", "192.0.2.10")
        with pytest.raises(Invalid) as caught:
            built.synthesize()
        assert "coin toss mail servers will grade" in str(
            caught.value
        )

    def test_the_choice_must_pick_among_the_truth(self):
        built = synthesizer()
        built.add_forward("blog.example.com.", "192.0.2.10")
        with pytest.raises(Invalid):
            built.choose_canonical(
                "192.0.2.10", "ghost.example.com."
            )
        built.choose_canonical(
            "192.0.2.10", "www.example.com."
        )
        zone = built.synthesize()
        assert zone["10.2.0.192.in-addr.arpa."] == (
            "www.example.com."
        )


class TestDrift:
    def test_both_directions_of_drift_are_named(self):
        built = synthesizer()
        findings = built.drift_audit(
            {
                "10.2.0.192.in-addr.arpa.": "old.example.com.",
                "9.9.0.192.in-addr.arpa.": "gone.example.com.",
            }
        )
        assert len(findings) == 3
        assert any(
            "hand says old.example.com., forward truth says "
            "www.example.com." in finding
            for finding in findings
        )
        assert any(
            "a world the forward zone no longer describes"
            in finding
            for finding in findings
        )
        assert any(
            "the address answers to nobody" in finding
            for finding in findings
        )

    def test_a_faithful_hand_zone_drifts_nowhere(self):
        built = synthesizer()
        assert built.drift_audit(built.synthesize()) == []
