from __future__ import annotations

import pytest

from beacon.consistentprefix import first_gap, is_prefix
from beacon.errors import Invalid


class TestPrefix:
    def test_a_contiguous_set_is_a_prefix(self):
        assert is_prefix({0, 1, 2, 3})

    def test_an_empty_set_is_a_prefix(self):
        assert is_prefix(set())

    def test_a_gapped_set_is_not_a_prefix(self):
        assert not is_prefix({0, 1, 3})

    def test_a_lagging_but_coherent_prefix_is_fine(self):
        # seeing only 0,1,2 while more exist is a valid older prefix
        assert is_prefix({0, 1, 2})


class TestGap:
    def test_the_gap_is_pointed_at(self):
        assert first_gap({0, 1, 3, 4}) == 2

    def test_a_coherent_prefix_has_no_gap_to_point_at(self):
        with pytest.raises(Invalid):
            first_gap({0, 1, 2})
