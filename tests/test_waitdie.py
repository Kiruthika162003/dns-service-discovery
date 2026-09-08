from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.waitdie import wait_die, waits_only_old_to_young


class TestWaitDie:
    def test_an_older_requester_waits(self):
        # smaller timestamp = older
        assert wait_die(requester_ts=1, holder_ts=5) == "wait"

    def test_a_younger_requester_dies(self):
        assert wait_die(requester_ts=5, holder_ts=1) == "die"

    def test_equal_timestamps_are_refused(self):
        with pytest.raises(Invalid):
            wait_die(3, 3)


class TestNoCycle:
    def test_waits_only_go_old_to_young(self):
        # whenever the scheme says wait, the requester is older
        assert waits_only_old_to_young(1, 5)
        # a younger requester dies rather than waits, so still holds
        assert waits_only_old_to_young(5, 1)
