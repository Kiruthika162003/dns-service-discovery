from __future__ import annotations

from beacon.causalbroadcast import deliver, deliverable


class TestDeliverability:
    def test_the_next_message_from_a_sender_is_deliverable(self):
        local = {"a": 0, "b": 0}
        message = {"a": 1}
        assert deliverable(local, message, sender="a")

    def test_a_message_skipping_one_is_held_back(self):
        local = {"a": 0}
        message = {"a": 2}  # we have not seen a's first
        assert not deliverable(local, message, sender="a")

    def test_a_dependency_on_an_unseen_third_party_holds(self):
        local = {"a": 0, "b": 0}
        # b's message depends on having seen a's first message
        message = {"a": 1, "b": 1}
        assert not deliverable(local, message, sender="b")

    def test_the_dependency_met_makes_it_deliverable(self):
        local = {"a": 1, "b": 0}
        message = {"a": 1, "b": 1}
        assert deliverable(local, message, sender="b")


class TestDeliver:
    def test_delivering_advances_the_local_clock(self):
        local = {"a": 0}
        assert deliver(local, {"a": 1}, sender="a") == {"a": 1}

    def test_a_reply_waits_for_its_cause(self):
        # a sends m1; b replies with m2 depending on m1.
        # a node that has not seen m1 cannot deliver m2 first.
        local = {"a": 0, "b": 0}
        reply = {"a": 1, "b": 1}
        assert not deliverable(local, reply, sender="b")
        after_cause = deliver(local, {"a": 1}, sender="a")
        assert deliverable(after_cause, reply, sender="b")
