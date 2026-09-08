from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.witnessreplica import data_copies_behind, durable, has_quorum


class TestQuorum:
    def test_witness_plus_one_replica_forms_a_majority(self):
        # 2 data replicas + 1 witness = 3 voters; need 2
        assert has_quorum(
            data_replicas_up=1, total_data_replicas=2, witness_up=True
        )

    def test_one_replica_alone_is_not_a_majority(self):
        assert not has_quorum(1, total_data_replicas=2, witness_up=False)

    def test_both_replicas_are_a_majority_without_the_witness(self):
        assert has_quorum(2, total_data_replicas=2, witness_up=False)

    def test_more_up_than_exist_is_refused(self):
        with pytest.raises(Invalid):
            has_quorum(3, total_data_replicas=2, witness_up=True)


class TestVoteIsNotACopy:
    def test_the_witness_adds_no_data_copy(self):
        # quorum met with 1 replica up, but only 1 real copy backs it
        assert has_quorum(1, 2, witness_up=True)
        assert data_copies_behind(1) == 1

    def test_at_least_one_data_replica_is_needed_for_durability(self):
        assert durable(1)
        assert not durable(0)
