from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.opcodes import code_of, dispatch


class TestDispatch:
    def test_a_query_routes_to_lookup(self):
        assert dispatch("QUERY") == "lookup"

    def test_notify_and_update_route_apart(self):
        assert dispatch("NOTIFY") == "zone-changed"
        assert dispatch("UPDATE") == "mutate-zone"

    def test_the_obsolete_iquery_is_notimp(self):
        with pytest.raises(Refused) as caught:
            dispatch("IQUERY")
        assert "obsoleted by RFC 3425" in str(caught.value)

    def test_an_unknown_opcode_is_refused(self):
        with pytest.raises(Invalid):
            dispatch("TELEPORT")


class TestCodes:
    def test_known_opcodes_have_numbers(self):
        assert code_of("QUERY") == 0
        assert code_of("UPDATE") == 5

    def test_an_unknown_opcode_has_no_number(self):
        with pytest.raises(Invalid):
            code_of("IQUERY")
