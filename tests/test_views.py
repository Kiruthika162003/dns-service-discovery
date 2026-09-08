from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.views import SplitHorizon, View


def horizon() -> SplitHorizon:
    built = SplitHorizon()
    built.add_view(
        View(
            name="inside",
            match_networks=("10.0.0.0/8",),
            answers={"www.corp.example.": "10.1.2.3"},
        )
    )
    built.add_view(
        View(
            name="outside",
            match_networks=("any",),
            answers={"www.corp.example.": "203.0.113.10"},
        )
    )
    return built


class TestTwoTruths:
    def test_the_office_sees_the_private_truth(self):
        answer = horizon().answer(
            "www.corp.example.", source="10.9.8.7"
        )
        assert "10.1.2.3 [view: inside]" in answer

    def test_home_sees_the_public_truth(self):
        answer = horizon().answer(
            "www.corp.example.", source="198.51.100.4"
        )
        assert "203.0.113.10 [view: outside]" in answer

    def test_every_answer_wears_its_view_stamp(self):
        answer = horizon().answer(
            "www.corp.example.", source="10.9.8.7"
        )
        assert "two dig outputs from two buildings" in answer

    def test_a_gap_in_a_view_names_the_view(self):
        with pytest.raises(Missing) as caught:
            horizon().answer(
                "ghost.corp.example.", source="10.9.8.7"
            )
        assert "no answer in view inside" in str(caught.value)

    def test_no_catchall_leaves_strangers_unanswered(self):
        built = SplitHorizon()
        built.add_view(
            View(
                name="inside",
                match_networks=("10.0.0.0/8",),
                answers={},
            )
        )
        with pytest.raises(Missing) as caught:
            built.answer("www.corp.example.", "198.51.100.4")
        assert "strangers unanswered" in str(caught.value)


class TestTheShadowLint:
    def test_a_clean_horizon_has_one_truth_per_network(self):
        assert "each network has one truth" in (
            horizon().shadow_lint()
        )

    def test_the_catchall_first_shadows_everyone_after(self):
        built = SplitHorizon()
        built.add_view(
            View(name="everything", match_networks=("any",))
        )
        built.add_view(
            View(name="inside", match_networks=("10.0.0.0/8",))
        )
        lint = built.shadow_lint()
        assert "1 shadowed entrie(s):" in lint
        assert (
            "view inside entry 10.0.0.0/8 is shadowed by "
            "view everything"
        ) in lint

    def test_duplicate_view_names_are_refused(self):
        built = horizon()
        with pytest.raises(Invalid):
            built.add_view(
                View(name="inside", match_networks=("any",))
            )
