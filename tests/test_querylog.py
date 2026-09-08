from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.querylog import QueryLog


def busy_log() -> QueryLog:
    log = QueryLog()
    for number in range(300):
        log.record(
            "10.0.0.5" if number % 3 else "10.0.0.9",
            "www.shop.example.",
            "NOERROR",
        )
    return log


class TestSampling:
    def test_one_in_a_hundred_keeps_the_receipts(self):
        log = busy_log()
        assert log.seen == 300
        assert len(log.sampled) == 3
        assert "keeps the receipts" in log.storage_bill()


class TestTopTalkers:
    def test_the_runaway_client_surfaces_first(self):
        talkers = busy_log().top_talkers(2)
        assert talkers[0] == "10.0.0.5: 200 query(ies)"
        assert talkers[1] == "10.0.0.9: 100 query(ies)"

    def test_a_top_list_needs_a_size(self):
        with pytest.raises(Invalid):
            busy_log().top_talkers(0)


class TestTheRcodeStory:
    def test_a_quiet_mix_is_just_a_number(self):
        story = busy_log().rcode_story()
        assert story == "300 query(ies), NXDOMAIN share 0%"

    def test_the_typo_storm_is_named_with_its_hostname(self):
        log = QueryLog()
        for _ in range(60):
            log.record(
                "10.0.0.7", "paymnets.shop.example.", "NXDOMAIN"
            )
        for _ in range(40):
            log.record(
                "10.0.0.5", "www.shop.example.", "NOERROR"
            )
        story = log.rcode_story()
        assert "NXDOMAIN share 60%" in story
        assert (
            "paymnets.shop.example. asked 60 time(s)"
        ) in story
        assert "one misspelled hostname multiplied" in story

    def test_no_queries_is_no_story(self):
        with pytest.raises(Invalid):
            QueryLog().rcode_story()
