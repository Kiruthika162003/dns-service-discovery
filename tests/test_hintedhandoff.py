from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.hintedhandoff import HintStore


class TestConstruction:
    def test_a_zero_capacity_store_is_refused(self):
        with pytest.raises(Refused):
            HintStore(0)


class TestStoreAndReplay:
    def test_hints_accumulate_per_replica(self):
        store = HintStore(capacity=10)
        store.store("r2", "write-a")
        store.store("r2", "write-b")
        store.store("r3", "write-c")
        assert store.pending("r2") == 2
        assert store.pending("r3") == 1

    def test_replay_returns_the_hints_in_order_and_clears(self):
        store = HintStore(capacity=10)
        store.store("r2", "write-a")
        store.store("r2", "write-b")
        assert store.replay("r2") == ["write-a", "write-b"]
        assert store.pending("r2") == 0

    def test_replaying_an_unknown_replica_is_empty(self):
        assert HintStore(10).replay("nobody") == []


class TestTheBound:
    def test_a_full_store_refuses_and_names_the_fallback(self):
        store = HintStore(capacity=2)
        store.store("r2", "w1")
        store.store("r2", "w2")
        with pytest.raises(Refused) as caught:
            store.store("r2", "w3")
        assert "anti-entropy repair" in str(caught.value)
