from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.validationstate import (
    ad_bit,
    describe,
    is_served_as_data,
    rcode_for,
)


class TestTheAdBit:
    def test_only_secure_earns_the_ad_bit(self):
        assert ad_bit("secure")
        assert not ad_bit("insecure")
        assert not ad_bit("indeterminate")

    def test_bogus_never_earns_ad(self):
        assert not ad_bit("bogus")


class TestBogusIsWithheld:
    def test_bogus_becomes_servfail(self):
        assert rcode_for("bogus") == "SERVFAIL"

    def test_bogus_is_not_served_as_data(self):
        assert not is_served_as_data("bogus")

    def test_the_other_states_are_served(self):
        assert is_served_as_data("secure")
        assert is_served_as_data("insecure")
        assert is_served_as_data("indeterminate")


class TestInsecureIsNotIndeterminate:
    def test_both_clear_ad_but_for_different_reasons(self):
        assert not ad_bit("insecure")
        assert not ad_bit("indeterminate")
        assert "proves the zone is unsigned" in describe("insecure")
        assert "silence is not proof" in describe("indeterminate")


class TestRefusals:
    def test_an_unknown_state_is_refused(self):
        with pytest.raises(Invalid):
            ad_bit("maybe")

    def test_describe_refuses_an_unknown_state(self):
        with pytest.raises(Invalid):
            describe("probably-fine")
