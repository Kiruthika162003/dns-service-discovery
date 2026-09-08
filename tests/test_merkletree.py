from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.merkletree import MerkleTree, divergent_keys


def base() -> dict[str, str]:
    return {f"k{i:04d}": f"v{i}" for i in range(1024)}


class TestRoot:
    def test_identical_trees_share_a_root(self):
        assert MerkleTree(base()).root() == MerkleTree(base()).root()

    def test_a_single_change_alters_the_root(self):
        other = base()
        other["k0500"] = "changed"
        assert MerkleTree(base()).root() != MerkleTree(other).root()

    def test_an_empty_tree_has_an_empty_root(self):
        assert MerkleTree({}).root() == ""


class TestDivergence:
    def test_identical_trees_report_no_divergence_cheaply(self):
        found, comparisons = divergent_keys(
            MerkleTree(base()), MerkleTree(base())
        )
        assert found == []
        assert comparisons == 1

    def test_one_diverged_key_is_found_in_log_comparisons(self):
        other = base()
        other["k0500"] = "changed"
        found, comparisons = divergent_keys(
            MerkleTree(base()), MerkleTree(other)
        )
        assert found == ["k0500"]
        # 1024 leaves -> depth 10, roughly 2 nodes per level
        assert comparisons < 30

    def test_multiple_divergences_are_all_found(self):
        other = base()
        other["k0001"] = "x"
        other["k1000"] = "y"
        found, _ = divergent_keys(
            MerkleTree(base()), MerkleTree(other)
        )
        assert found == ["k0001", "k1000"]


class TestRefusals:
    def test_different_key_sets_are_refused(self):
        with pytest.raises(Invalid) as caught:
            divergent_keys(
                MerkleTree({"a": "1"}), MerkleTree({"b": "1"})
            )
        assert "diverged values, not added or removed" in str(
            caught.value
        )
