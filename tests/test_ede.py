from __future__ import annotations

import pytest

from beacon.ede import ExtendedError, annotate, divide
from beacon.errors import Invalid


class TestClassification:
    def test_bogus_is_a_network_fault(self):
        error = annotate("SERVFAIL", 6)
        assert error.fault == "network"
        assert not error.is_policy()

    def test_blocked_is_a_policy_refusal(self):
        error = annotate("REFUSED", 15)
        assert error.is_policy()
        assert error.purport == "blocked"

    def test_an_unknown_code_invents_a_reason_and_is_refused(self):
        with pytest.raises(Invalid) as caught:
            annotate("SERVFAIL", 999)
        assert "invents a reason" in str(caught.value)


class TestRetryAdvice:
    def test_a_fault_on_a_retryable_rcode_may_retry(self):
        assert annotate("SERVFAIL", 7).should_retry()

    def test_a_policy_refusal_is_never_retried(self):
        assert not annotate("REFUSED", 16).should_retry()

    def test_a_noerror_fault_is_not_retried(self):
        assert not annotate("NOERROR", 3).should_retry()


class TestRendering:
    def test_the_render_carries_the_note_and_the_advice(self):
        line = annotate(
            "SERVFAIL", 6, "chain of trust broken at example."
        ).render()
        assert "dnssec-bogus" in line
        assert "chain of trust broken" in line
        assert "retry is allowed" in line

    def test_a_policy_render_says_do_not_retry(self):
        line = annotate("REFUSED", 18).render()
        assert "do not retry" in line

    def test_the_division_counts_both_moral_categories(self):
        report = divide(
            [
                annotate("SERVFAIL", 6),
                annotate("REFUSED", 15),
                annotate("REFUSED", 16),
            ]
        )
        assert "1 fault(s) worth retrying" in report
        assert "2 policy refusal(s)" in report
        assert "never changes the rcode" in report


class TestTheRcodeIsSacred:
    def test_the_annotation_preserves_the_rcode(self):
        error = ExtendedError("SERVFAIL", 6)
        assert error.rcode == "SERVFAIL"
