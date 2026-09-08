from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.leadertransfer import transfer


class TestTransfer:
    def test_a_caught_up_target_gets_the_signal(self):
        assert (
            transfer(
                target_last_index=10,
                leader_last_index=10,
                accepting_entries=False,
            )
            == "send-timeout-now"
        )


class TestPreconditions:
    def test_a_leader_still_accepting_entries_is_refused(self):
        with pytest.raises(Refused) as caught:
            transfer(10, 10, accepting_entries=True)
        assert "stop first" in str(caught.value)

    def test_a_lagging_target_is_refused(self):
        with pytest.raises(Refused) as caught:
            transfer(7, 10, accepting_entries=False)
        assert "strands the cluster" in str(caught.value)
