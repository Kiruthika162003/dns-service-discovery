from __future__ import annotations

import pytest

from beacon.cnameflatten import flatten
from beacon.errors import Invalid, Loop


class TestFlatten:
    def test_a_chain_resolves_to_the_terminal_data(self):
        zone = {
            "www.example.": ("cname", "web.example."),
            "web.example.": ("cname", "host.example."),
            "host.example.": ("data", ["192.0.2.1"]),
        }
        terminal, chain, data = flatten(zone, "www.example.")
        assert terminal == "host.example."
        assert chain == ["www.example.", "web.example."]
        assert data == ["192.0.2.1"]

    def test_a_direct_data_name_returns_itself(self):
        zone = {"host.example.": ("data", ["192.0.2.1"])}
        terminal, chain, _ = flatten(zone, "host.example.")
        assert terminal == "host.example."
        assert chain == []


class TestGuards:
    def test_a_loop_is_refused(self):
        zone = {
            "a.example.": ("cname", "b.example."),
            "b.example.": ("cname", "a.example."),
        }
        with pytest.raises(Loop):
            flatten(zone, "a.example.")

    def test_an_out_of_zone_target_stops_the_flatten(self):
        zone = {"www.example.": ("cname", "elsewhere.net.")}
        with pytest.raises(Invalid) as caught:
            flatten(zone, "www.example.")
        assert "referral to chase" in str(caught.value)
