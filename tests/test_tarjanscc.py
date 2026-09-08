from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tarjanscc import components


class TestComponents:
    def test_two_cycles_joined_by_one_edge(self):
        adjacency = {0: [1], 1: [2], 2: [0, 3], 3: [4], 4: [5], 5: [3]}
        assert components(6, adjacency) == [[0, 1, 2], [3, 4, 5]]

    def test_an_acyclic_graph_has_singleton_components(self):
        adjacency = {0: [1], 1: [2]}
        assert components(3, adjacency) == [[0], [1], [2]]

    def test_a_single_cycle_is_one_component(self):
        adjacency = {0: [1], 1: [2], 2: [0]}
        assert components(3, adjacency) == [[0, 1, 2]]

    def test_an_isolated_vertex_is_its_own_component(self):
        assert components(1, {}) == [[0]]


class TestRefusals:
    def test_an_edge_to_a_missing_vertex_is_refused(self):
        with pytest.raises(Invalid):
            components(2, {0: [5]})

    def test_a_negative_vertex_count_is_refused(self):
        with pytest.raises(Invalid):
            components(-1, {})
