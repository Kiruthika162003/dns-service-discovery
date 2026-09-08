from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.topologicalsort import topological_sort


class TestOrder:
    def test_dependencies_come_before_dependents(self):
        # c depends on b, b on a
        deps = {"a": set(), "b": {"a"}, "c": {"b"}}
        assert topological_sort(deps) == ["a", "b", "c"]

    def test_independent_nodes_are_ordered_deterministically(self):
        deps = {"a": set(), "b": set(), "c": {"a", "b"}}
        order = topological_sort(deps)
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")

    def test_a_dependency_named_but_not_keyed_is_included(self):
        # "root" appears only as a dependency
        deps = {"leaf": {"root"}}
        assert topological_sort(deps) == ["root", "leaf"]


class TestCycle:
    def test_a_cycle_is_refused(self):
        deps = {"a": {"b"}, "b": {"a"}}
        with pytest.raises(Invalid) as caught:
            topological_sort(deps)
        assert "circular dependency" in str(caught.value)

    def test_a_self_dependency_is_a_cycle(self):
        with pytest.raises(Invalid):
            topological_sort({"a": {"a"}})
