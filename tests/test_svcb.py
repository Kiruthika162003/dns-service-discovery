from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.svcb import SvcbRecord, SvcbSet


class TestRecordRules:
    def test_an_alias_carries_no_parameters(self):
        with pytest.raises(Invalid) as caught:
            SvcbRecord(0, "svc.example.", {"alpn": "h3"})
        assert "it is a redirect" in str(caught.value)

    def test_a_service_target_of_dot_is_alias_only(self):
        with pytest.raises(Invalid) as caught:
            SvcbRecord(1, ".", {"alpn": "h2"})
        assert "only legal in AliasMode" in str(caught.value)

    def test_a_negative_priority_is_refused(self):
        with pytest.raises(Invalid):
            SvcbRecord(-1, "svc.example.")


class TestSetInvariants:
    def test_an_alias_must_stand_alone(self):
        with pytest.raises(Invalid) as caught:
            SvcbSet(
                "example.",
                [
                    SvcbRecord(0, "svc.example."),
                    SvcbRecord(1, "a.example.", {"alpn": "h2"}),
                ],
            )
        assert "must stand alone" in str(caught.value)

    def test_the_alias_target_is_followed_not_ordered(self):
        chosen = SvcbSet("example.", [SvcbRecord(0, "svc.example.")])
        assert chosen.is_alias_form()
        assert chosen.alias_target() == "svc.example."
        with pytest.raises(Invalid):
            chosen.ordered()


class TestSelection:
    def build(self) -> SvcbSet:
        return SvcbSet(
            "example.",
            [
                SvcbRecord(3, "c.example.", {"alpn": "h2"}),
                SvcbRecord(1, "a.example.", {"alpn": "h3,h2"}, weight=5),
                SvcbRecord(1, "b.example.", {"alpn": "h2"}, weight=9),
            ],
        )

    def test_lowest_priority_wins_then_highest_weight(self):
        first = self.build().first_choice()
        assert first.priority == 1
        assert first.target == "b.example."

    def test_the_order_is_a_preference_list(self):
        ordered = self.build().ordered()
        assert [r.target for r in ordered] == [
            "b.example.",
            "a.example.",
            "c.example.",
        ]

    def test_h3_is_detected_when_any_record_offers_it(self):
        assert self.build().supports_h3()

    def test_no_h3_when_nobody_offers_it(self):
        plain = SvcbSet(
            "example.",
            [SvcbRecord(1, "a.example.", {"alpn": "h2"})],
        )
        assert not plain.supports_h3()
