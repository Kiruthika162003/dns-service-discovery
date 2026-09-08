from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ricartagrawala import may_enter, should_defer


class TestDefer:
    def test_a_holder_defers_every_request(self):
        assert should_defer("held", 0, "a", 5, "b")

    def test_a_wanter_defers_a_later_request(self):
        # I want it at ts 2; an incoming request at ts 5 is later -> defer
        assert should_defer("wanted", 2, "a", 5, "b")

    def test_a_wanter_replies_to_an_earlier_request(self):
        # incoming ts 1 beats my ts 3 -> I reply, do not defer
        assert not should_defer("wanted", 3, "a", 1, "b")

    def test_an_idle_node_always_replies(self):
        assert not should_defer("idle", 0, "a", 5, "b")

    def test_an_unknown_state_is_refused(self):
        with pytest.raises(Invalid):
            should_defer("busy", 0, "a", 1, "b")


class TestEnter:
    def test_unanimous_replies_permit_entry(self):
        assert may_enter(replies_received=3, total_others=3)

    def test_a_missing_reply_blocks_entry(self):
        assert not may_enter(replies_received=2, total_others=3)

    def test_more_replies_than_peers_is_refused(self):
        with pytest.raises(Invalid):
            may_enter(replies_received=4, total_others=3)
