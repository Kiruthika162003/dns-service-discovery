from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.twophaselocking import TwoPhaseLock, compatible


class TestCompatibility:
    def test_two_shared_locks_coexist(self):
        assert compatible("shared", "shared")

    def test_an_exclusive_lock_excludes_everyone(self):
        assert not compatible("exclusive", "shared")
        assert not compatible("shared", "exclusive")
        assert not compatible("exclusive", "exclusive")


class TestPhaseRule:
    def test_it_acquires_during_the_growing_phase(self):
        txn = TwoPhaseLock()
        txn.acquire("a", "shared")
        txn.acquire("b", "exclusive")
        assert txn.phase == "growing"

    def test_releasing_enters_the_shrinking_phase(self):
        txn = TwoPhaseLock()
        txn.acquire("a", "shared")
        txn.release("a")
        assert txn.phase == "shrinking"

    def test_acquiring_after_a_release_is_refused(self):
        txn = TwoPhaseLock()
        txn.acquire("a", "shared")
        txn.release("a")
        with pytest.raises(Invalid) as caught:
            txn.acquire("b", "shared")
        assert "breaks\nserializability" in caught.value.args[0] or (
            "breaks serializability" in str(caught.value)
        )

    def test_an_unknown_mode_is_refused(self):
        with pytest.raises(Invalid):
            TwoPhaseLock().acquire("a", "maybe")
