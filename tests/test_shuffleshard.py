from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.shuffleshard import ShuffleShard

WORKERS = tuple(f"w{number}" for number in range(8))
TENANTS = [f"tenant-{number}" for number in range(29)]


def shard() -> ShuffleShard:
    return ShuffleShard(workers=WORKERS, hand_size=2)


class TestHands:
    def test_hands_are_deterministic_and_sorted(self):
        assert shard().hand_for("tenant-0") == ("w1", "w2")
        assert shard().hand_for("tenant-0") == (
            shard().hand_for("tenant-0")
        )

    def test_a_zero_hand_plays_nothing(self):
        with pytest.raises(Invalid):
            ShuffleShard(workers=WORKERS, hand_size=0)

    def test_a_deck_sized_hand_is_plain_sharding(self):
        with pytest.raises(Invalid) as caught:
            ShuffleShard(workers=("a", "b"), hand_size=2)
        assert "with extra steps" in str(caught.value)


class TestTheBlast:
    def test_one_of_twenty_eight_shares_the_whole_hand(self):
        report = shard().blast_report("tenant-0", TENANTS)
        assert (
            "of 28 other tenant(s), 1 lost everything, 13 "
            "lost part of a hand, 14 untouched"
        ) in report
        assert "fully shared hands: tenant-21" in report

    def test_the_plain_sharding_comparison_is_printed(self):
        report = shard().blast_report("tenant-0", TENANTS)
        assert (
            "plain sharding would take roughly 7 co-tenant(s) "
            "down whole"
        ) in report
        assert "exists to shrink" in report

    def test_the_poison_must_be_in_the_population(self):
        with pytest.raises(Invalid):
            shard().blast_report("stranger", TENANTS)
