from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rpz import PolicyRule, evaluate


def rules() -> list[PolicyRule]:
    return [
        PolicyRule("example.", "nxdomain"),
        PolicyRule("safe.example.", "passthru"),
        PolicyRule("ads.net.", "redirect", "warning.local."),
    ]


class TestSpecificity:
    def test_the_broad_block_catches_a_bare_subdomain(self):
        result = evaluate("evil.example.", rules())
        assert result.action == "nxdomain"

    def test_a_narrower_passthru_wins_for_its_subtree(self):
        result = evaluate("safe.example.", rules())
        assert result.action == "passthru"

    def test_the_passthru_extends_to_deeper_names(self):
        result = evaluate("api.safe.example.", rules())
        assert result.action == "passthru"


class TestActions:
    def test_a_redirect_carries_its_target(self):
        result = evaluate("tracker.ads.net.", rules())
        assert result.action == "redirect"
        assert result.target == "warning.local."

    def test_an_unmatched_name_passes_through_by_default(self):
        result = evaluate("unrelated.org.", rules())
        assert result.action == "passthru"


class TestConstruction:
    def test_an_unknown_action_is_refused(self):
        with pytest.raises(Invalid):
            PolicyRule("x.", "quarantine")

    def test_a_targetless_redirect_is_refused(self):
        with pytest.raises(Invalid) as caught:
            PolicyRule("x.", "redirect")
        assert "rewrites to nothing" in str(caught.value)
