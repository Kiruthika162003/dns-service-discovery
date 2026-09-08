from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.names import Name
from beacon.qname import (
    privacy_report,
    resolve_minimized,
    resolve_traditional,
)

MAIL = Name.parse("mail.eng.corp.example")


class TestTheLeak:
    def test_traditional_resolution_leaks_to_every_server(self):
        result = resolve_traditional(MAIL)
        assert result.servers_that_saw_full_name == 4
        assert all("FULL" in step for step in result.steps)

    def test_the_root_resolves_itself(self):
        with pytest.raises(Invalid):
            resolve_traditional(Name.parse("."))


class TestMinimization:
    def test_only_the_final_authority_sees_the_full_name(self):
        result = resolve_minimized(MAIL, zone_cuts={1, 2, 3, 4})
        assert result.servers_that_saw_full_name == 1
        assert result.steps[0] == "revealed only example."
        assert result.steps[-1] == (
            "revealed only mail.eng.corp.example."
        )

    def test_clean_cuts_add_no_extra_queries(self):
        result = resolve_minimized(MAIL, zone_cuts={1, 2, 3, 4})
        assert result.extra_queries == 0

    def test_misguessed_cuts_cost_a_query_per_label(self):
        result = resolve_minimized(MAIL, zone_cuts={2, 4})
        assert result.extra_queries == 2


class TestThePrivacyReport:
    def test_the_report_prices_the_privacy(self):
        report = privacy_report(MAIL, zone_cuts={2, 4})
        assert (
            "traditionally 4 server(s) learned the full name"
        ) in report
        assert "3 fewer eavesdropper(s)" in report
        assert "cost of 2 extra query(ies)" in report
        assert "advocacy, not engineering" in report
