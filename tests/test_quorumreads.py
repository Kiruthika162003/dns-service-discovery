from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.quorumreads import (
    QuorumConfig,
    read_report,
    resolve_read,
)


class TestTheOverlapRule:
    def test_r_plus_w_over_n_is_strongly_consistent(self):
        config = QuorumConfig(
            replicas=3, read_quorum=2, write_quorum=2
        )
        assert config.strongly_consistent()
        assert "strongly consistent" in config.verdict()

    def test_r_plus_w_under_n_can_miss_a_write(self):
        config = QuorumConfig(
            replicas=5, read_quorum=1, write_quorum=1
        )
        assert not config.strongly_consistent()
        assert "whether you meant it or not" in config.verdict()

    def test_the_boundary_needs_strictly_greater(self):
        config = QuorumConfig(
            replicas=4, read_quorum=2, write_quorum=2
        )
        assert not config.strongly_consistent()

    def test_out_of_range_quorums_are_refused(self):
        with pytest.raises(Invalid):
            QuorumConfig(replicas=3, read_quorum=4, write_quorum=2)
        with pytest.raises(Invalid):
            QuorumConfig(replicas=3, read_quorum=2, write_quorum=0)


class TestResolution:
    def test_the_highest_version_wins_and_stale_is_counted(self):
        value, stale = resolve_read(
            [("old", 4), ("new", 7), ("old", 4)]
        )
        assert value == "new"
        assert stale == 2

    def test_an_empty_quorum_answered_nothing(self):
        with pytest.raises(Invalid):
            resolve_read([])


class TestTheReport:
    def test_a_thin_quorum_must_not_pretend(self):
        config = QuorumConfig(
            replicas=3, read_quorum=2, write_quorum=2
        )
        with pytest.raises(Invalid) as caught:
            read_report(config, [("v", 1)])
        assert "must not pretend it can" in str(caught.value)

    def test_the_stale_count_is_an_early_warning(self):
        config = QuorumConfig(
            replicas=3, read_quorum=2, write_quorum=2
        )
        report = read_report(
            config, [("new", 7), ("old", 4)]
        )
        assert "1 of 2 replica(s) were behind" in report
        assert "early warning of a replica drifting" in report

    def test_a_fresh_quorum_carries_no_warning(self):
        config = QuorumConfig(
            replicas=3, read_quorum=2, write_quorum=2
        )
        report = read_report(
            config, [("new", 7), ("new", 7)]
        )
        assert "0 of 2 replica(s) were behind" in report
        assert "early warning" not in report
