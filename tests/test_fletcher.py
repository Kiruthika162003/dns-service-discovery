from __future__ import annotations

from beacon.fletcher import fletcher16, plain_sum


class TestChecksum:
    def test_it_is_deterministic(self):
        assert fletcher16(b"beacon") == fletcher16(b"beacon")

    def test_different_content_differs(self):
        assert fletcher16(b"beacon") != fletcher16(b"beacom")

    def test_the_empty_input_is_zero(self):
        assert fletcher16(b"") == 0


class TestTransposition:
    def test_a_transposition_changes_the_fletcher_checksum(self):
        assert fletcher16(b"ab") != fletcher16(b"ba")

    def test_a_transposition_does_not_change_the_plain_sum(self):
        # the weakness Fletcher fixes: a plain sum is blind to order
        assert plain_sum(b"ab") == plain_sum(b"ba")
