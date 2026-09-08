from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.sortlist import on_link, sort_addresses


class TestOnLink:
    def test_same_subnet_is_on_link(self):
        assert on_link("192.0.2.10", "192.0.2.200", prefix=24)

    def test_different_subnet_is_off_link(self):
        assert not on_link("192.0.2.10", "198.51.100.1", prefix=24)

    def test_a_bad_prefix_is_refused(self):
        with pytest.raises(Invalid):
            on_link("192.0.2.10", "192.0.2.11", prefix=40)


class TestSorting:
    def test_on_link_addresses_move_to_the_front(self):
        client = "192.0.2.10"
        addresses = [
            "198.51.100.1",
            "192.0.2.50",
            "203.0.113.9",
            "192.0.2.99",
        ]
        result = sort_addresses(client, addresses)
        assert result[:2] == ["192.0.2.50", "192.0.2.99"]

    def test_within_tier_order_is_preserved(self):
        client = "10.0.0.1"
        # all off-link; order must be untouched
        addresses = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
        assert sort_addresses(client, addresses) == addresses

    def test_the_stable_sort_keeps_remote_order_after_locals(self):
        client = "192.0.2.10"
        addresses = ["8.8.8.8", "192.0.2.5", "1.1.1.1"]
        assert sort_addresses(client, addresses) == [
            "192.0.2.5",
            "8.8.8.8",
            "1.1.1.1",
        ]
