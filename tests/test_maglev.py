from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.maglev import MaglevTable, disruption

BACKENDS = ["b0", "b1", "b2", "b3", "b4"]
KEYS = [f"key-{i}" for i in range(3000)]


class TestConstruction:
    def test_a_non_prime_size_is_refused(self):
        with pytest.raises(Invalid) as caught:
            MaglevTable(BACKENDS, size=100)
        assert "is not prime" in str(caught.value)

    def test_a_table_too_small_starves_a_backend(self):
        with pytest.raises(Invalid) as caught:
            MaglevTable(["a", "b", "c", "d", "e"], size=5)
        assert "would starve one" in str(caught.value)

    def test_an_empty_pool_is_refused(self):
        with pytest.raises(Invalid):
            MaglevTable([], size=97)


class TestEvenness:
    def test_every_slot_names_a_backend(self):
        table = MaglevTable(BACKENDS, size=97)
        assert all(index >= 0 for index in table.entry)

    def test_the_load_is_close_to_even(self):
        table = MaglevTable(BACKENDS, size=97)
        assert table.spread() <= 2

    def test_lookup_is_stable(self):
        table = MaglevTable(BACKENDS, size=97)
        assert table.lookup("key-1") == table.lookup("key-1")


class TestMinimalDisruption:
    def test_dropping_a_backend_stirs_little(self):
        before = MaglevTable(BACKENDS, size=97)
        after = MaglevTable(BACKENDS[:-1], size=97)
        fraction = disruption(before, after, KEYS)
        assert fraction < 0.40

    def test_the_survivors_keep_most_of_their_keys(self):
        before = MaglevTable(BACKENDS, size=97)
        after = MaglevTable(BACKENDS[:-1], size=97)
        kept = sum(
            1
            for key in KEYS
            if before.lookup(key) == after.lookup(key)
        )
        assert kept > len(KEYS) * 0.6
