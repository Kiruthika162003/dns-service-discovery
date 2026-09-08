from __future__ import annotations

import pytest

from beacon.dname import covers, rewrite
from beacon.errors import Invalid


class TestRewrite:
    def test_a_descendant_is_rewritten_to_the_target(self):
        assert (
            rewrite("host.old.example.", "old.example.", "new.example.")
            == "host.new.example."
        )

    def test_a_deep_descendant_keeps_its_prefix(self):
        assert (
            rewrite("a.b.old.example.", "old.example.", "new.example.")
            == "a.b.new.example."
        )

    def test_the_owner_itself_is_not_rewritten(self):
        with pytest.raises(Invalid) as caught:
            rewrite("old.example.", "old.example.", "new.example.")
        assert "separate CNAME" in str(caught.value)

    def test_a_name_outside_the_subtree_is_refused(self):
        with pytest.raises(Invalid):
            rewrite("host.other.", "old.example.", "new.example.")


class TestCovers:
    def test_a_descendant_is_covered(self):
        assert covers("host.old.example.", "old.example.")

    def test_the_owner_is_not_covered(self):
        assert not covers("old.example.", "old.example.")
