from __future__ import annotations

import pytest

from beacon.bulkhead import Bulkhead
from beacon.errors import Invalid, Refused


class TestConstruction:
    def test_no_compartments_is_refused(self):
        with pytest.raises(Invalid):
            Bulkhead({})

    def test_a_zero_limit_compartment_is_refused(self):
        with pytest.raises(Invalid):
            Bulkhead({"db": 0})


class TestIsolation:
    def test_a_saturated_compartment_refuses_its_own_calls(self):
        bulkhead = Bulkhead({"db": 2, "cache": 2})
        bulkhead.acquire("db")
        bulkhead.acquire("db")
        with pytest.raises(Refused) as caught:
            bulkhead.acquire("db")
        assert "the other dependencies are" in str(caught.value)

    def test_a_full_compartment_does_not_block_the_others(self):
        bulkhead = Bulkhead({"db": 1, "cache": 1})
        bulkhead.acquire("db")
        # db is full, cache is untouched
        bulkhead.acquire("cache")
        assert bulkhead.saturated() == ["cache", "db"]

    def test_release_frees_the_compartment(self):
        bulkhead = Bulkhead({"db": 1})
        bulkhead.acquire("db")
        bulkhead.release("db")
        bulkhead.acquire("db")
        assert bulkhead.saturated() == ["db"]


class TestRefusals:
    def test_an_unknown_dependency_is_refused(self):
        with pytest.raises(Invalid):
            Bulkhead({"db": 1}).acquire("ghost")

    def test_a_double_release_is_refused(self):
        bulkhead = Bulkhead({"db": 1})
        with pytest.raises(Invalid):
            bulkhead.release("db")
