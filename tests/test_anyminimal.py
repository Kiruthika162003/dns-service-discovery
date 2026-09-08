from __future__ import annotations

import pytest

from beacon.anyminimal import (
    SYNTHETIC_HINFO,
    amplification_factor,
    answer,
    report,
)
from beacon.errors import NoData


def rrsets() -> dict[str, list[str]]:
    return {
        "A": ["192.0.2.1", "192.0.2.2", "192.0.2.3"],
        "AAAA": ["2001:db8::1", "2001:db8::2"],
        "MX": ["10 mail.example.", "20 mail2.example."],
        "TXT": ["v=spf1 -all"],
    }


class TestMinimalAny:
    def test_minimal_any_returns_one_synthetic_record(self):
        result = answer("ANY", rrsets(), minimal=True)
        assert result == [SYNTHETIC_HINFO]

    def test_full_any_returns_every_record(self):
        result = answer("ANY", rrsets(), minimal=False)
        assert len(result) == 8


class TestSpecificQueriesAreUntouched:
    def test_a_specific_type_returns_its_full_rrset(self):
        assert answer("A", rrsets()) == [
            "192.0.2.1",
            "192.0.2.2",
            "192.0.2.3",
        ]

    def test_a_specific_missing_type_is_nodata_not_minimized(self):
        with pytest.raises(NoData) as caught:
            answer("SRV", rrsets())
        assert "never minimized" in str(caught.value)


class TestTheLeverage:
    def test_the_amplification_is_the_full_count_over_one(self):
        assert amplification_factor(rrsets()) == 8.0

    def test_the_report_names_the_removed_leverage(self):
        line = report(rrsets())
        assert "an amplification of 8x" in line
        assert "a specific query is untouched" in line
