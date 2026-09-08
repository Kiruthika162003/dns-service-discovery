from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tlsa import bypasses_ca, matches, rejects_misissued


class TestMatching:
    def test_a_matching_digest_passes(self):
        assert matches("abc123", "abc123", usage=3)

    def test_a_different_digest_fails(self):
        assert not matches("abc123", "def456", usage=3)

    def test_an_unknown_usage_is_refused(self):
        with pytest.raises(Invalid):
            matches("a", "a", usage=9)


class TestUsage:
    def test_dane_usages_bypass_the_ca(self):
        assert bypasses_ca(2)
        assert bypasses_ca(3)

    def test_pkix_usages_do_not(self):
        assert not bypasses_ca(0)
        assert not bypasses_ca(1)


class TestMisissuance:
    def test_a_valid_but_unpinned_cert_is_rejected_under_dane_ee(self):
        # usage 3, the presented cert is valid but not the pinned one
        assert rejects_misissued(usage=3, presented_is_pinned=False)

    def test_the_pinned_cert_is_accepted(self):
        assert not rejects_misissued(usage=3, presented_is_pinned=True)
