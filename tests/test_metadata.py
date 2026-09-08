from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.metadata import MetadataRegistry


def registry() -> MetadataRegistry:
    built = MetadataRegistry()
    built.register(
        "b1",
        {"version": "3.1", "zone": "eu", "region": "emea"},
    )
    built.register(
        "b2",
        {"version": "3.2", "zone": "eu", "region": "emea"},
    )
    built.register(
        "b3",
        {"version": "3.2", "zone": "us", "region": "emea"},
    )
    return built


class TestSelection:
    def test_selection_is_set_logic(self):
        assert registry().select({"zone": "eu"}) == ["b1", "b2"]

    def test_a_two_tag_predicate_narrows_further(self):
        assert registry().select(
            {"version": "3.2", "zone": "eu"}
        ) == ["b2"]

    def test_a_typo_tag_is_refused_not_returned_empty(self):
        with pytest.raises(Invalid) as caught:
            registry().select({"zne": "eu"})
        assert "trains clients to distrust empty" in str(
            caught.value
        )

    def test_selecting_over_nothing_is_missing(self):
        with pytest.raises(Missing):
            MetadataRegistry().select({"zone": "eu"})


class TestTheAudits:
    def test_the_always_true_tag_is_pure_overhead(self):
        findings = registry().always_true_audit()
        assert len(findings) == 1
        assert findings[0].startswith("region carries one value")
        assert "narrows nothing" in findings[0]

    def test_a_varying_tag_is_not_overhead(self):
        findings = registry().always_true_audit()
        assert not any(
            finding.startswith("zone") for finding in findings
        )

    def test_the_schema_report_counts_the_overhead(self):
        report = registry().schema_report()
        assert "3 instance(s), 3 tag key(s), 1 narrowing nothing" in (
            report
        )

    def test_double_registration_is_refused(self):
        built = registry()
        with pytest.raises(Invalid):
            built.register("b1", {})
