from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.negcache import AggressiveNegCache, CoveredRange


class TestCoverage:
    def test_a_normal_range_covers_its_interior(self):
        covered = CoveredRange(low="alpha", high="gamma")
        assert covered.covers("beta")
        assert not covered.covers("omega")

    def test_a_wraparound_range_covers_the_ends(self):
        covered = CoveredRange(low="omega", high="alpha")
        assert covered.covers("zzz")
        assert covered.covers("aardvark")
        assert not covered.covers("beta")


class TestTheCache:
    def test_the_first_miss_caches_the_whole_gap(self):
        cache = AggressiveNegCache()
        verdict = cache.query(
            "beta.", lambda _name: ("alpha.", "gamma.")
        )
        assert "the whole gap alpha...gamma. cached" in verdict
        assert cache.upstream_queries == 1

    def test_the_next_name_in_the_gap_is_free(self):
        cache = AggressiveNegCache()
        cache.query("beta.", lambda _name: ("alpha.", "gamma."))
        verdict = cache.query(
            "beto.", lambda _name: ("alpha.", "gamma.")
        )
        assert "no upstream query" in verdict
        assert cache.range_hits == 1
        assert cache.upstream_queries == 1

    def test_a_zero_width_range_is_not_a_proof(self):
        with pytest.raises(Invalid) as caught:
            AggressiveNegCache().learn_range("x", "x")
        assert "a point, not a proof of absence" in str(
            caught.value
        )


class TestTheFlood:
    def test_the_flood_collapses_to_one_query(self):
        cache = AggressiveNegCache()
        names = [f"sub{number}.example." for number in range(50)]
        report = cache.flood_report(
            names, lambda _name: ("a", "zzzz")
        )
        assert "per-name caching pays 50 upstream queries" in (
            report
        )
        assert "range caching pays 1, saving 49" in report
        assert "the gain lives in wide gaps" in report

    def test_an_empty_flood_is_refused(self):
        with pytest.raises(Invalid):
            AggressiveNegCache().flood_report(
                [], lambda _name: ("a", "z")
            )
