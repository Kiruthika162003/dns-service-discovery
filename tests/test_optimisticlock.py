from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.optimisticlock import OptimisticStore


class TestCommit:
    def test_a_first_write_commits(self):
        store = OptimisticStore()
        _, version = store.read("k")
        assert store.commit("k", version, "v1") == 1

    def test_an_uncontended_update_commits(self):
        store = OptimisticStore()
        store.commit("k", 0, "v1")
        _, version = store.read("k")
        assert store.commit("k", version, "v2") == 2


class TestConflict:
    def test_a_stale_write_is_refused(self):
        store = OptimisticStore()
        store.commit("k", 0, "v1")  # version now 1
        # a transaction that read version 0 tries to commit
        with pytest.raises(Invalid) as caught:
            store.commit("k", 0, "based-on-stale")
        assert "abort and retry" in str(caught.value)

    def test_retrying_from_the_new_version_succeeds(self):
        store = OptimisticStore()
        store.commit("k", 0, "v1")
        _, fresh = store.read("k")
        assert store.commit("k", fresh, "v2") == 2

    def test_the_loser_of_a_race_does_not_overwrite(self):
        store = OptimisticStore()
        # both read version 0
        _, a = store.read("k")
        _, b = store.read("k")
        store.commit("k", a, "from-a")
        with pytest.raises(Invalid):
            store.commit("k", b, "from-b")
        assert store.read("k")[0] == "from-a"
