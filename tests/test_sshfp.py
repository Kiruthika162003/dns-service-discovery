from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.sshfp import strong_enough, verify

# (algorithm, fp_type, fingerprint); 4 = Ed25519, 2 = SHA-256
RECORDS = [(4, 2, "abc123"), (1, 2, "rsa-fp")]


class TestVerify:
    def test_a_matching_key_verifies(self):
        assert verify(RECORDS, key_algorithm=4, presented_fingerprint="abc123")

    def test_a_wrong_fingerprint_fails(self):
        assert not verify(RECORDS, key_algorithm=4, presented_fingerprint="evil")

    def test_a_wrong_algorithm_fails(self):
        assert not verify(RECORDS, key_algorithm=3, presented_fingerprint="abc123")

    def test_an_unknown_fp_type_is_refused(self):
        with pytest.raises(Invalid):
            verify(RECORDS, 4, "abc123", fp_type=9)


class TestStrength:
    def test_sha256_is_strong_enough(self):
        assert strong_enough(2)

    def test_sha1_is_not(self):
        assert not strong_enough(1)
