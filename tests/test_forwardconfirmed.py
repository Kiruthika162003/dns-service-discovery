from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.forwardconfirmed import confirmed, failure_reason

PTR = {"192.0.2.5": "mail.example.", "192.0.2.9": "liar.example."}
FORWARD = {
    "mail.example.": ["192.0.2.5"],
    "liar.example.": ["192.0.2.99"],  # does not point back
}


class TestConfirmed:
    def test_a_matching_pair_confirms(self):
        assert confirmed("192.0.2.5", PTR, FORWARD)

    def test_a_forward_that_omits_the_address_fails(self):
        assert not confirmed("192.0.2.9", PTR, FORWARD)

    def test_a_missing_ptr_cannot_begin(self):
        with pytest.raises(Invalid):
            confirmed("203.0.113.1", PTR, FORWARD)


class TestReason:
    def test_a_confirmed_pair_reads_confirmed(self):
        assert failure_reason("192.0.2.5", PTR, FORWARD) == "confirmed"

    def test_a_missing_ptr_reads_no_ptr(self):
        assert failure_reason("203.0.113.1", PTR, FORWARD) == "no-ptr"

    def test_a_mismatch_reads_forward_mismatch(self):
        assert failure_reason("192.0.2.9", PTR, FORWARD) == (
            "forward-mismatch"
        )
