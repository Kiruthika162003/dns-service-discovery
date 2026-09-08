from __future__ import annotations

from beacon.chandylamport import is_consistent_cut, offending_message


# messages as (sender, send_seq, receiver, recv_seq)
class TestConsistent:
    def test_a_cut_recording_both_send_and_receive_is_consistent(self):
        messages = [("p", 1, "q", 1)]
        cut = {"p": 2, "q": 2}  # both events before the cut
        assert is_consistent_cut(messages, cut)

    def test_a_cut_recording_neither_is_consistent(self):
        messages = [("p", 5, "q", 5)]
        cut = {"p": 2, "q": 2}  # both after the cut
        assert is_consistent_cut(messages, cut)

    def test_a_send_recorded_without_its_receive_is_consistent(self):
        # an in-flight message: sent before the cut, received after
        messages = [("p", 1, "q", 9)]
        cut = {"p": 2, "q": 2}
        assert is_consistent_cut(messages, cut)


class TestInconsistent:
    def test_a_receive_without_its_send_is_inconsistent(self):
        # effect (receive) recorded, cause (send) not: impossible state
        messages = [("p", 9, "q", 1)]
        cut = {"p": 2, "q": 2}
        assert not is_consistent_cut(messages, cut)

    def test_the_offending_message_is_pointed_at(self):
        messages = [("p", 1, "q", 1), ("p", 9, "q", 1)]
        cut = {"p": 2, "q": 2}
        assert offending_message(messages, cut) == ("p", 9, "q", 1)

    def test_a_consistent_cut_has_no_offender(self):
        assert offending_message([("p", 1, "q", 1)], {"p": 2, "q": 2}) is None
