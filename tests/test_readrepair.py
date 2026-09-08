from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.readrepair import is_converged, resolve


class TestResolve:
    def test_the_newest_version_wins(self):
        responses = {
            "r1": ("old", 3),
            "r2": ("new", 5),
            "r3": ("old", 3),
        }
        value, version, _stale = resolve(responses)
        assert value == "new"
        assert version == 5

    def test_the_stale_replicas_are_named_for_repair(self):
        responses = {
            "r1": ("old", 3),
            "r2": ("new", 5),
            "r3": ("old", 3),
        }
        _, _, stale = resolve(responses)
        assert stale == ["r1", "r3"]

    def test_converged_replicas_need_no_repair(self):
        responses = {"r1": ("v", 7), "r2": ("v", 7)}
        assert is_converged(responses)


class TestRefusals:
    def test_no_responses_is_refused(self):
        with pytest.raises(Invalid):
            resolve({})
