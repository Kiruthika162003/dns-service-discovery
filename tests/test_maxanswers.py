from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.maxanswers import AnswerSizer

INSTANCES = tuple(f"10.0.0.{number}" for number in range(20))
QUERY_IDS = [f"q-{number}" for number in range(200)]


def sizer() -> AnswerSizer:
    return AnswerSizer(instances=INSTANCES, subset_size=6)


class TestSizing:
    def test_the_answer_is_bounded_to_the_budget(self):
        assert len(sizer().answer_for("q-0")) == 6

    def test_the_subset_is_deterministic(self):
        assert sizer().answer_for("q-7") == sizer().answer_for(
            "q-7"
        )

    def test_a_small_fleet_fits_one_answer(self):
        small = AnswerSizer(
            instances=("a", "b", "c"), subset_size=6
        )
        assert small.answer_for("q-0") == ["a", "b", "c"]

    def test_an_empty_name_answers_nothing(self):
        with pytest.raises(Invalid):
            AnswerSizer(instances=())


class TestCoverage:
    def test_rotation_covers_the_fleet_eventually(self):
        assert sizer().queries_to_cover(QUERY_IDS) == 11

    def test_the_report_names_the_coverage_query_count(self):
        report = sizer().coverage_report(QUERY_IDS)
        assert "the full fleet is first seen after 11" in report
        assert "hides ninety instances from every answer" in (
            report
        )

    def test_a_fitting_fleet_hides_nobody(self):
        small = AnswerSizer(
            instances=("a", "b"), subset_size=6
        )
        assert "no instance hidden" in small.coverage_report(
            ["q-0"]
        )

    def test_too_few_queries_leave_instances_unseen(self):
        report = sizer().coverage_report(["q-0", "q-1"])
        assert "some remain unseen" in report
        assert "idle capacity nobody chose to idle" in report
