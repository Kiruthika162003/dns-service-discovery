from __future__ import annotations

import pytest

from beacon.errors import Invalid, Loop
from beacon.httpschain import resolve_endpoint


class TestFollowing:
    def test_a_chain_terminates_at_the_service_mode_name(self):
        aliases = {
            "www.example.": "svc.example.",
            "svc.example.": "edge.example.",
            "edge.example.": None,
        }
        assert resolve_endpoint(aliases, "www.example.") == "edge.example."

    def test_a_name_that_is_already_terminal_returns_itself(self):
        assert resolve_endpoint({"a.": None}, "a.") == "a."

    def test_a_name_absent_from_the_map_is_terminal(self):
        assert resolve_endpoint({}, "unknown.") == "unknown."


class TestGuards:
    def test_a_cycle_is_caught(self):
        aliases = {"a.": "b.", "b.": "a."}
        with pytest.raises(Loop) as caught:
            resolve_endpoint(aliases, "a.")
        assert "followed forever" in str(caught.value)

    def test_an_overlong_chain_is_refused(self):
        aliases = {f"n{i}.": f"n{i + 1}." for i in range(20)}
        aliases["n20."] = None
        with pytest.raises(Invalid) as caught:
            resolve_endpoint(aliases, "n0.", max_hops=8)
        assert "exceeds 8 hops" in str(caught.value)
