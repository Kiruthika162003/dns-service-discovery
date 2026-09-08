from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.priming import prime


class TestPriming:
    def test_the_live_set_is_adopted_whole(self):
        result = prime({"a.root", "b.root"}, {"a.root", "b.root"})
        assert result.adopted == frozenset({"a.root", "b.root"})
        assert not result.dropped
        assert not result.added

    def test_a_decommissioned_root_is_dropped(self):
        result = prime(
            {"a.root", "old.root"}, {"a.root", "b.root"}
        )
        assert result.dropped == frozenset({"old.root"})
        assert result.added == frozenset({"b.root"})

    def test_the_adopted_set_never_keeps_a_stale_hint(self):
        result = prime({"old.root"}, {"a.root"})
        assert "old.root" not in result.adopted

    def test_priming_from_an_empty_answer_is_refused(self):
        with pytest.raises(Invalid) as caught:
            prime({"a.root"}, set())
        assert "would strand it with no roots" in str(caught.value)

    def test_the_summary_counts_the_churn(self):
        result = prime(
            {"a.root", "old.root"}, {"a.root", "b.root"}
        )
        line = result.summary()
        assert "dropped 1 stale" in line
        assert "adopted 1 new" in line
