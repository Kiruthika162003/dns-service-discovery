from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.multiquestion import validate_qdcount


class TestTheOneLegalValue:
    def test_exactly_one_question_is_valid(self):
        assert validate_qdcount(1) == 1

    def test_more_than_one_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_qdcount(2)
        assert "half-answered" in str(caught.value)


class TestEmptyQuestion:
    def test_a_query_with_no_question_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_qdcount(0, opcode="QUERY")
        assert "asks nothing" in str(caught.value)

    def test_notify_may_carry_an_empty_question(self):
        assert validate_qdcount(0, opcode="NOTIFY") == 0

    def test_update_may_carry_an_empty_question(self):
        assert validate_qdcount(0, opcode="UPDATE") == 0


class TestRefusals:
    def test_a_negative_count_is_refused(self):
        with pytest.raises(Invalid):
            validate_qdcount(-1)
