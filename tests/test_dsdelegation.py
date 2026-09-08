from __future__ import annotations

import pytest

from beacon.dsdelegation import TrustChain
from beacon.errors import Invalid


def chain() -> TrustChain:
    built = TrustChain()
    built.add_zone(".", "root-key-fp", parent=None)
    built.add_zone("com.", "com-key-fp", parent=".")
    built.add_zone(
        "example.com.", "example-key-fp", parent="com."
    )
    built.publish_ds("com.", "com-key-fp")
    built.publish_ds("example.com.", "example-key-fp")
    built.trust_root(".")
    return built


class TestTheIntactChain:
    def test_the_chain_walks_to_the_trusted_root(self):
        verdict = chain().validate("example.com.")
        assert "trust chain intact through 3 zone(s)" in verdict
        assert "to the trusted root ." in verdict


class TestTheBreaks:
    def test_the_stale_link_is_the_commonest_outage(self):
        built = chain()
        built.zones["example.com."].key_fingerprint = (
            "rotated-fp"
        )
        verdict = built.validate("example.com.")
        assert verdict.startswith("STALE LINK")
        assert "valid signatures nobody vouches for" in verdict

    def test_the_missing_link_is_an_orphan(self):
        built = chain()
        del built.parent_records["example.com."]
        verdict = built.validate("example.com.")
        assert verdict.startswith("MISSING LINK")
        assert "an orphan with no papers" in verdict

    def test_the_broken_root_floats_the_chain(self):
        built = chain()
        built.trusted_roots.clear()
        verdict = built.validate("example.com.")
        assert verdict.startswith("BROKEN ROOT")
        assert "the whole chain floats" in verdict


class TestChainDiscipline:
    def test_publishing_ds_for_a_stranger_is_refused(self):
        with pytest.raises(Invalid):
            chain().publish_ds("ghost.", "fp")

    def test_double_adding_a_zone_is_refused(self):
        built = chain()
        with pytest.raises(Invalid):
            built.add_zone("com.", "x", parent=".")

    def test_validating_a_stranger_is_refused(self):
        with pytest.raises(Invalid):
            chain().validate("other.net.")
