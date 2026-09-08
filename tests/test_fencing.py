from __future__ import annotations

import pytest

from beacon.errors import Fenced, Invalid
from beacon.fencing import FencedResource


class TestMonotonic:
    def test_increasing_tokens_are_accepted(self):
        resource = FencedResource()
        assert resource.accept(1) == "accepted"
        assert resource.accept(2) == "accepted"
        assert resource.accept(5) == "accepted"

    def test_the_same_token_is_still_accepted(self):
        resource = FencedResource()
        resource.accept(3)
        assert resource.accept(3) == "accepted"


class TestFencing:
    def test_a_stale_token_is_fenced_out(self):
        resource = FencedResource()
        resource.accept(5)  # a newer holder wrote
        with pytest.raises(Fenced) as caught:
            resource.accept(3)  # paused old holder wakes
        assert "a newer holder exists" in str(caught.value)

    def test_would_accept_previews_without_committing(self):
        resource = FencedResource()
        resource.accept(5)
        assert not resource.would_accept(3)
        assert resource.would_accept(6)
        # preview did not advance the highest
        assert resource.accept(5) == "accepted"


class TestRefusals:
    def test_a_nonpositive_token_is_refused(self):
        with pytest.raises(Invalid):
            FencedResource().accept(0)
