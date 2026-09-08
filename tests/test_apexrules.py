from __future__ import annotations

import pytest

from beacon.apexrules import flatten_alias, validate_apex, validate_name
from beacon.errors import Invalid


class TestApex:
    def test_a_valid_apex_carries_soa_and_ns(self):
        assert validate_apex({"SOA", "NS", "MX"}) == "apex valid"

    def test_a_cname_at_the_apex_is_forbidden(self):
        with pytest.raises(Invalid) as caught:
            validate_apex({"SOA", "NS", "CNAME"})
        assert "ALIAS flattening exists instead" in str(
            caught.value
        )

    def test_an_apex_missing_ns_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_apex({"SOA"})
        assert "missing NS" in str(caught.value)


class TestOrdinaryNames:
    def test_a_lone_cname_is_fine(self):
        assert validate_name({"CNAME"}) == "name valid"

    def test_a_cname_beside_other_data_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_name({"CNAME", "A"})
        assert "owns no records of its own" in str(caught.value)

    def test_ordinary_data_without_cname_is_fine(self):
        assert validate_name({"A", "AAAA", "TXT"}) == "name valid"


class TestAliasFlattening:
    def test_flattening_yields_apex_a_records(self):
        result = flatten_alias("example.", ["192.0.2.1", "192.0.2.2"])
        assert result == [
            ("example.", "A", "192.0.2.1"),
            ("example.", "A", "192.0.2.2"),
        ]

    def test_flattening_to_no_addresses_is_refused(self):
        with pytest.raises(Invalid) as caught:
            flatten_alias("example.", [])
        assert "empty apex is worse than a slow one" in str(
            caught.value
        )
