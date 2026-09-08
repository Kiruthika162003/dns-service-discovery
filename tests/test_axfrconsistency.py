from __future__ import annotations

import pytest

from beacon.axfrconsistency import validate_axfr
from beacon.errors import Invalid


class TestConsistency:
    def test_a_matching_serial_bracket_is_consistent(self):
        records = [
            ("SOA", 42),
            ("A", None),
            ("NS", None),
            ("SOA", 42),
        ]
        assert validate_axfr(records) == "consistent snapshot"

    def test_a_serial_that_moved_is_refused(self):
        records = [("SOA", 42), ("A", None), ("SOA", 43)]
        with pytest.raises(Invalid) as caught:
            validate_axfr(records)
        assert "straddles two versions" in str(caught.value)


class TestFraming:
    def test_a_missing_opening_soa_is_refused(self):
        records = [("A", None), ("SOA", 42)]
        with pytest.raises(Invalid) as caught:
            validate_axfr(records)
        assert "open and close on the SOA" in str(caught.value)

    def test_a_too_short_stream_is_refused(self):
        with pytest.raises(Invalid):
            validate_axfr([("SOA", 42)])
