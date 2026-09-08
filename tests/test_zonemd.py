from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.zonemd import compute_digest, detects_missing_record, verify

ZONE = [
    "example. SOA ns1 admin 1 2 3 4 5",
    "example. NS ns1.example.",
    "www.example. A 192.0.2.1",
]


class TestDigest:
    def test_the_digest_is_order_independent(self):
        assert compute_digest(ZONE) == compute_digest(list(reversed(ZONE)))

    def test_an_empty_zone_is_refused(self):
        with pytest.raises(Invalid):
            compute_digest([])


class TestVerify:
    def test_a_matching_digest_verifies(self):
        digest = compute_digest(ZONE)
        assert verify(ZONE, digest)

    def test_a_tampered_zone_fails(self):
        digest = compute_digest(ZONE)
        tampered = [*ZONE[:2], "www.example. A 6.6.6.6"]
        assert not verify(tampered, digest)


class TestTruncation:
    def test_a_missing_record_is_detected(self):
        assert detects_missing_record(ZONE, ZONE[:2])

    def test_the_intact_file_is_not_flagged(self):
        assert not detects_missing_record(ZONE, list(ZONE))
