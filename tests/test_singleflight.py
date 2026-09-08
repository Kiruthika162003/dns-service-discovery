from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.singleflight import SingleFlight


class TestCoalescing:
    def test_the_first_request_leads(self):
        flight = SingleFlight()
        assert flight.begin("popular.example.") == "leader"

    def test_later_requests_join(self):
        flight = SingleFlight()
        flight.begin("popular.example.")
        assert flight.begin("popular.example.") == "joined"
        assert flight.begin("popular.example.") == "joined"
        assert flight.waiters("popular.example.") == 3

    def test_different_keys_lead_separately(self):
        flight = SingleFlight()
        assert flight.begin("a.example.") == "leader"
        assert flight.begin("b.example.") == "leader"


class TestLifecycle:
    def test_completing_clears_the_flight(self):
        flight = SingleFlight()
        flight.begin("k")
        flight.begin("k")
        assert flight.complete("k") == 2
        # a request after completion starts fresh
        assert flight.begin("k") == "leader"

    def test_completing_an_absent_flight_is_refused(self):
        with pytest.raises(Invalid):
            SingleFlight().complete("nothing")


class TestSaving:
    def test_the_herd_collapses_to_one_upstream(self):
        flight = SingleFlight()
        for _ in range(1000):
            flight.begin("hot")
        assert flight.upstream_saved(1000, "hot") == 999
