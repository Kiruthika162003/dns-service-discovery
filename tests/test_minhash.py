from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.minhash import signature, similarity


class TestSimilarity:
    def test_identical_sets_are_fully_similar(self):
        items = {f"e{i}" for i in range(100)}
        sig = signature(items, num_hashes=64)
        assert similarity(sig, sig) == 1.0

    def test_disjoint_sets_are_nearly_dissimilar(self):
        a = signature({f"a{i}" for i in range(100)}, 64)
        b = signature({f"b{i}" for i in range(100)}, 64)
        assert similarity(a, b) < 0.2

    def test_overlapping_sets_estimate_the_jaccard(self):
        # 50 shared of a 150-element union -> Jaccard 1/3
        shared = {f"s{i}" for i in range(50)}
        a = shared | {f"a{i}" for i in range(50)}
        b = shared | {f"b{i}" for i in range(50)}
        estimate = similarity(signature(a, 256), signature(b, 256))
        assert 0.2 < estimate < 0.45


class TestRefusals:
    def test_mismatched_signature_lengths_are_refused(self):
        with pytest.raises(Invalid):
            similarity([1, 2, 3], [1, 2])

    def test_an_empty_set_is_refused(self):
        with pytest.raises(Invalid):
            signature(set(), 8)
