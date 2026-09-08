from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.selectiveack import (
    cumulative_ack,
    retransmit_with_sack,
    retransmit_without_sack,
)


class TestCumulative:
    def test_it_names_the_first_gap(self):
        # 0,1,2 received, 3 missing, 4 received
        assert cumulative_ack({0, 1, 2, 4}) == 3

    def test_a_full_prefix_advances_fully(self):
        assert cumulative_ack({0, 1, 2, 3}) == 4


class TestRetransmit:
    def test_without_sack_resends_the_whole_tail(self):
        # got 0,1,2,4,5 ; 3 missing ; highest sent 5
        assert retransmit_without_sack({0, 1, 2, 4, 5}, highest_sent=5) == {
            3,
            4,
            5,
        }

    def test_with_sack_resends_only_the_hole(self):
        assert retransmit_with_sack({0, 1, 2, 4, 5}, highest_sent=5) == {3}

    def test_sack_saves_when_gaps_are_scattered(self):
        received = {0, 1, 3, 5}
        plain = retransmit_without_sack(received, highest_sent=5)
        sacked = retransmit_with_sack(received, highest_sent=5)
        assert sacked == {2, 4}
        assert len(sacked) < len(plain)

    def test_a_negative_highest_is_refused(self):
        with pytest.raises(Invalid):
            retransmit_with_sack({0}, highest_sent=-1)
