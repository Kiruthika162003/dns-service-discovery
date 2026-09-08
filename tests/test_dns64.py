from __future__ import annotations

import pytest

from beacon.dns64 import (
    dns64_answer,
    synthesize_one,
    was_synthesized,
)
from beacon.errors import Invalid, NoData


class TestSynthesis:
    def test_the_address_embeds_in_the_prefix(self):
        assert synthesize_one("192.0.2.1") == "64:ff9b::c000:0201"

    def test_a_bad_address_is_refused(self):
        with pytest.raises(Invalid):
            synthesize_one("192.0.2")

    def test_a_synthetic_address_is_recognizable(self):
        assert was_synthesized("64:ff9b::c000:0201")
        assert not was_synthesized("2001:db8::1")


class TestAnswerRules:
    def test_missing_aaaa_synthesizes_from_a(self):
        answer = dns64_answer([], ["192.0.2.1", "192.0.2.9"])
        assert answer == ["64:ff9b::c000:0201", "64:ff9b::c000:0209"]

    def test_a_native_aaaa_is_never_overridden(self):
        with pytest.raises(Invalid) as caught:
            dns64_answer(["2001:db8::1"], ["192.0.2.1"])
        assert "could strand it" in str(caught.value)

    def test_no_a_to_synthesize_from_is_nodata(self):
        with pytest.raises(NoData) as caught:
            dns64_answer([], [])
        assert "no IPv4 one" in str(caught.value)
