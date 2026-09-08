from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.visibilityqueue import VisibilityQueue


class TestConstruction:
    def test_a_zero_timeout_is_refused(self):
        with pytest.raises(Invalid):
            VisibilityQueue(timeout=0)


class TestDelivery:
    def test_a_received_message_is_hidden(self):
        queue = VisibilityQueue(timeout=30)
        queue.send("m1")
        assert queue.receive(now=0) == "m1"
        # hidden, so a second receive finds nothing yet
        assert queue.receive(now=1) is None

    def test_a_deleted_message_never_reappears(self):
        queue = VisibilityQueue(timeout=30)
        queue.send("m1")
        queue.receive(now=0)
        queue.delete("m1")
        assert queue.receive(now=100) is None


class TestAtLeastOnce:
    def test_a_crashed_consumer_gets_the_message_redelivered(self):
        queue = VisibilityQueue(timeout=30)
        queue.send("m1")
        queue.receive(now=0)  # consumer takes it, then crashes
        # past the timeout, the message returns to visibility
        assert queue.receive(now=31) == "m1"

    def test_depth_reflects_reclaimed_messages(self):
        queue = VisibilityQueue(timeout=30)
        queue.send("m1")
        queue.receive(now=0)
        assert queue.depth(now=0) == 0
        assert queue.depth(now=31) == 1
