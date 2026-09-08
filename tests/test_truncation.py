from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.truncation import TransportLedger


class TestTheFlag:
    def test_a_small_answer_fits_the_datagram(self):
        ledger = TransportLedger()
        verdict = ledger.answer(4)
        assert "320 bytes: fits the datagram" in verdict

    def test_the_large_answer_truncates_and_retries(self):
        ledger = TransportLedger()
        verdict = ledger.answer(12)
        assert "truncated at 6" in verdict
        assert "handshake tax 2 tick(s)" in verdict
        assert "full answer delivered" in verdict

    def test_declining_the_retry_is_degraded_not_wrong(self):
        ledger = TransportLedger()
        verdict = ledger.answer(12, client_retries=False)
        assert "truncation flag SET" in verdict
        assert "degraded, not wrong" in verdict
        assert ledger.tcp_retries == 0

    def test_silent_truncation_is_refused_outright(self):
        ledger = TransportLedger()
        with pytest.raises(Invalid) as caught:
            ledger.silent_truncation(12)
        assert "confidently wrong" in str(caught.value)
        assert "worst state a distributed system offers" in str(
            caught.value
        )

    def test_an_empty_answer_needs_records(self):
        with pytest.raises(Invalid):
            TransportLedger().answer(0)


class TestTheShape:
    def test_the_habitual_truncator_is_named(self):
        ledger = TransportLedger()
        for _ in range(4):
            ledger.answer(12)
        for _ in range(4):
            ledger.answer(2)
        report = ledger.shape_report()
        assert "4 truncated (50%)" in report
        assert "zone-shape complaint" in report

    def test_the_occasional_truncation_is_just_transport(self):
        ledger = TransportLedger()
        for _ in range(9):
            ledger.answer(2)
        ledger.answer(12)
        assert "zone-shape" not in ledger.shape_report()
