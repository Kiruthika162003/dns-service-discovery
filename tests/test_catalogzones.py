from __future__ import annotations

import pytest

from beacon.catalogzones import Catalog, reconcile, summary
from beacon.errors import Invalid


def catalog() -> Catalog:
    return Catalog(
        version=2,
        members={
            "a1b2": "one.example.",
            "c3d4": "two.example.",
        },
    )


class TestSchema:
    def test_an_unknown_version_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Catalog(version=3, members={})
        assert "might mean things it would misread" in str(
            caught.value
        )

    def test_a_zone_under_two_labels_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Catalog(
                version=2,
                members={"x": "dup.example.", "y": "dup.example."},
            )
        assert "identified twice" in str(caught.value)


class TestReconcile:
    def test_new_members_are_added(self):
        to_add, to_remove = reconcile({"one.example."}, catalog())
        assert to_add == {"two.example."}
        assert to_remove == set()

    def test_vanished_members_are_removed(self):
        to_add, to_remove = reconcile(
            {"one.example.", "two.example.", "gone.example."},
            catalog(),
        )
        assert to_remove == {"gone.example."}
        assert to_add == set()

    def test_the_summary_counts_the_churn(self):
        line = summary({"one.example."}, catalog())
        assert "add 1, remove 0" in line
        assert "2 member zone(s)" in line
