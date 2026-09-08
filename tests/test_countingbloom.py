from __future__ import annotations

import pytest

from beacon.countingbloom import CountingBloom
from beacon.errors import Invalid


class TestMembership:
    def test_an_added_item_is_present(self):
        cbf = CountingBloom(size=256, num_hashes=4)
        cbf.add("a")
        assert cbf.contains("a")

    def test_a_removed_item_is_absent(self):
        cbf = CountingBloom(size=256, num_hashes=4)
        cbf.add("a")
        cbf.remove("a")
        assert not cbf.contains("a")

    def test_removing_one_of_two_leaves_the_other(self):
        cbf = CountingBloom(size=1024, num_hashes=5)
        cbf.add("a")
        cbf.add("b")
        cbf.remove("a")
        assert cbf.contains("b")


class TestUnderflow:
    def test_removing_a_never_added_item_is_refused(self):
        cbf = CountingBloom(size=256, num_hashes=4)
        with pytest.raises(Invalid) as caught:
            cbf.remove("never")
        assert "pair with prior adds" in str(caught.value)

    def test_a_bad_construction_is_refused(self):
        with pytest.raises(Invalid):
            CountingBloom(size=0, num_hashes=4)
