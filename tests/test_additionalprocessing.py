from __future__ import annotations

from beacon.additionalprocessing import additional_for, dropped_targets

APEX = "example."
ADDRESSES = {
    "mail.example.": ["192.0.2.5"],
    "ns1.example.": ["192.0.2.53"],
}


class TestGlue:
    def test_in_zone_targets_get_their_addresses(self):
        glue = additional_for(
            ["mail.example."], ADDRESSES, APEX
        )
        assert glue == {"mail.example.": ["192.0.2.5"]}

    def test_out_of_zone_targets_are_not_vouched_for(self):
        glue = additional_for(
            ["mail.example.", "mx.other."], ADDRESSES, APEX
        )
        assert "mx.other." not in glue

    def test_an_in_zone_target_without_an_address_yields_nothing(
        self,
    ):
        glue = additional_for(["ftp.example."], ADDRESSES, APEX)
        assert glue == {}


class TestDropped:
    def test_dropped_lists_the_out_of_zone_targets(self):
        dropped = dropped_targets(
            ["mail.example.", "mx.other.", "a.elsewhere."], APEX
        )
        assert dropped == ["a.elsewhere.", "mx.other."]

    def test_all_in_zone_drops_nothing(self):
        assert dropped_targets(["mail.example."], APEX) == []
