from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.jointconsensus import joint_majority, single_majority

OLD = {"a", "b", "c"}
NEW = {"c", "d", "e"}


class TestJointMajority:
    def test_a_vote_carrying_both_majorities_passes(self):
        # need >1 of old and >1 of new: {b,c,d} has b,c in old and c,d in new
        assert joint_majority({"b", "c", "d"}, OLD, NEW)

    def test_a_majority_of_only_the_old_set_fails(self):
        # {a,b} is a majority of OLD but not of NEW
        assert not joint_majority({"a", "b"}, OLD, NEW)

    def test_a_majority_of_only_the_new_set_fails(self):
        assert not joint_majority({"d", "e"}, OLD, NEW)

    def test_an_empty_config_is_refused(self):
        with pytest.raises(Invalid):
            joint_majority({"a"}, set(), NEW)


class TestSingleMajority:
    def test_a_majority_of_one_config(self):
        assert single_majority({"a", "b"}, OLD)
        assert not single_majority({"a"}, OLD)

    def test_an_empty_config_is_refused(self):
        with pytest.raises(Invalid):
            single_majority({"a"}, set())
