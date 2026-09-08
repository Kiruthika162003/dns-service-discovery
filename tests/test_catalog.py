from __future__ import annotations

import pytest

from beacon.catalog import VersionedCatalog
from beacon.errors import Invalid, Lagging


def catalog() -> VersionedCatalog:
    built = VersionedCatalog()
    built.register("billing", "b1")
    built.register("billing", "b2")
    built.register("search", "s1")
    return built


class TestVersions:
    def test_every_mutation_mints_a_version(self):
        assert catalog().version == 3

    def test_a_repeat_registration_wakes_nobody(self):
        chosen = catalog()
        with pytest.raises(Invalid) as caught:
            chosen.register("billing", "b1")
        assert "wake every watcher for nothing" in str(
            caught.value
        )
        assert chosen.version == 3


class TestWatching:
    def test_the_caught_up_watcher_gets_cheap_nothing(self):
        assert catalog().watch(seen_version=3) == []

    def test_the_behind_watcher_gets_only_the_delta(self):
        chosen = catalog()
        changes = chosen.watch(seen_version=1)
        assert [(c.action, c.instance) for c in changes] == [
            ("add", "b2"),
            ("add", "s1"),
        ]

    def test_nobody_has_seen_the_future(self):
        with pytest.raises(Invalid):
            catalog().watch(seen_version=9)

    def test_falling_off_the_window_demands_a_snapshot(self):
        chosen = catalog()
        for number in range(20):
            chosen.register("churn", f"c{number}")
        with pytest.raises(Lagging) as caught:
            chosen.watch(seen_version=1)
        assert "never existed at any version" in str(
            caught.value
        )

    def test_the_snapshot_resyncs_the_stale(self):
        chosen = catalog()
        version, entries = chosen.snapshot()
        assert version == 3
        assert entries["billing"] == {"b1", "b2"}


class TestTheLedger:
    def test_watching_undercuts_polling(self):
        chosen = catalog()
        chosen.watch(seen_version=0)
        for _ in range(9):
            chosen.watch(seen_version=3)
        ledger = chosen.bandwidth_ledger(polls_replaced=10)
        assert (
            "watching cost 12 byte-unit(s) where polling "
            "costs 1000"
        ) in ledger

    def test_the_comparison_needs_polls(self):
        with pytest.raises(Invalid):
            catalog().bandwidth_ledger(polls_replaced=0)
