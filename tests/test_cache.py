from __future__ import annotations

import pytest

from beacon.cache import TtlCache
from beacon.errors import Invalid
from beacon.names import Name
from beacon.records import Record

WWW = Name.parse("www.example.com")


def a_record(ttl: int = 300) -> Record:
    return Record(name=WWW, rtype="A", value="192.0.2.10", ttl=ttl)


class TestPositiveCaching:
    def test_a_hit_serves_the_remaining_ttl_not_the_original(self):
        cache = TtlCache()
        cache.store(WWW, "A", [a_record(300)], now=100)
        kind, _, remaining = cache.lookup(WWW, "A", now=250)
        assert kind == "ANSWER"
        assert remaining == 150

    def test_the_set_caches_under_its_smallest_ttl(self):
        cache = TtlCache()
        verdict = cache.store(
            WWW, "A", [a_record(300), a_record(60)], now=0
        )
        assert "cached for 60 tick(s), the smallest ttl" in verdict

    def test_expiry_happens_on_contact_not_in_the_background(self):
        cache = TtlCache()
        cache.store(WWW, "A", [a_record(100)], now=0)
        assert cache.lookup(WWW, "A", now=100) is None
        assert cache.expiries_on_contact == 1

    def test_ttl_zero_is_never_cached(self):
        cache = TtlCache()
        verdict = cache.store(WWW, "A", [a_record(0)], now=0)
        assert "the cache does not" in verdict
        assert cache.lookup(WWW, "A", now=1) is None

    def test_an_empty_positive_is_a_category_error(self):
        with pytest.raises(Invalid) as caught:
            TtlCache().store(WWW, "A", [], now=0)
        assert "store it as one" in str(caught.value)


class TestNegativeCaching:
    def test_nxdomain_answers_for_every_type(self):
        cache = TtlCache()
        cache.store_negative(
            WWW, "NXDOMAIN", now=0, negative_ttl=300
        )
        for rtype in ("A", "AAAA", "TXT"):
            kind, _, _ = cache.lookup(WWW, rtype, now=10)
            assert kind == "NXDOMAIN"
        assert cache.negative_saves == 3

    def test_nodata_answers_only_its_own_type(self):
        cache = TtlCache()
        cache.store_negative(
            WWW, "NODATA", now=0, negative_ttl=300, rtype="TXT"
        )
        kind, _, _ = cache.lookup(WWW, "TXT", now=10)
        assert kind == "NODATA"
        assert cache.lookup(WWW, "A", now=10) is None

    def test_a_typeless_nodata_would_poison_the_name(self):
        with pytest.raises(Invalid) as caught:
            TtlCache().store_negative(
                WWW, "NODATA", now=0, negative_ttl=300
            )
        assert "poisons types never asked" in str(caught.value)

    def test_negative_entries_expire_like_any_answer(self):
        cache = TtlCache()
        cache.store_negative(
            WWW, "NXDOMAIN", now=0, negative_ttl=50
        )
        assert cache.lookup(WWW, "A", now=50) is None


class TestTheLedger:
    def test_the_four_columns_are_kept_apart(self):
        cache = TtlCache()
        cache.store(WWW, "A", [a_record(100)], now=0)
        cache.lookup(WWW, "A", now=10)
        cache.lookup(WWW, "AAAA", now=10)
        cache.store_negative(
            WWW, "NODATA", now=10, negative_ttl=60, rtype="TXT"
        )
        cache.lookup(WWW, "TXT", now=20)
        ledger = cache.ledger()
        assert "1 hit(s), 1 miss(es)" in ledger
        assert "1 negative save(s)" in ledger
        assert "because the cache remembered a no" in ledger
