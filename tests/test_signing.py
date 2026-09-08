from __future__ import annotations

import pytest

from beacon.errors import Expired, Invalid
from beacon.signing import Signature, Validator


def signature(
    inception: int = 100, expiration: int = 1000
) -> Signature:
    return Signature(
        signer_key="zsk-2026",
        inception=inception,
        expiration=expiration,
    )


def validator() -> Validator:
    return Validator(zone_key="zsk-2026")


class TestTheWindow:
    def test_a_backward_window_signs_nothing(self):
        with pytest.raises(Invalid):
            Signature(
                signer_key="k", inception=10, expiration=5
            )

    def test_forever_is_a_replay_attacks_best_friend(self):
        with pytest.raises(Invalid) as caught:
            Signature(
                signer_key="k",
                inception=0,
                expiration=3_000_000,
            )
        assert "replay attack's best friend" in str(caught.value)

    def test_the_wrong_signer_is_not_the_zone(self):
        with pytest.raises(Invalid) as caught:
            Validator(zone_key="other").validate(
                signature(), now=500
            )
        assert "it is not the zone" in str(caught.value)


class TestSkew:
    def test_inside_the_window_is_plainly_valid(self):
        assert validator().validate(signature(), now=500) == (
            "valid"
        )

    def test_a_minute_of_skew_does_not_invalidate_the_world(self):
        chosen = validator()
        verdict = chosen.validate(signature(), now=97)
        assert "within the skew grace" in verdict
        assert chosen.skew_saves == 1

    def test_beyond_the_grace_the_future_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validator().validate(signature(), now=90)
        assert "a replay from tomorrow or a broken clock" in (
            str(caught.value)
        )

    def test_past_the_grace_the_expiry_is_final(self):
        with pytest.raises(Expired) as caught:
            validator().validate(signature(), now=1006)
        assert "nothing re-signed" in str(caught.value)


class TestTheHorizon:
    def test_the_countdown_names_the_nearest_wall(self):
        report = validator().horizon_report(
            [signature(), signature(expiration=2000)], now=500
        )
        assert "the nearest wall is 500 tick(s) away" in report

    def test_the_close_wall_gets_the_scheduled_outage_line(self):
        report = validator().horizon_report(
            [signature(expiration=600)], now=500
        )
        assert "scheduled months in advance" in report

    def test_the_wall_itself_is_all_capitals(self):
        report = validator().horizon_report(
            [signature(expiration=400)], now=500
        )
        assert report.startswith("THE WALL")
