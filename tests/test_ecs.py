from __future__ import annotations

import pytest

from beacon.ecs import (
    ScopedAnswer,
    entries_under,
    fragmentation_report,
    truncate,
)
from beacon.errors import Invalid


class TestTruncation:
    def test_a_slash_24_zeroes_the_last_octet(self):
        assert truncate("203.0.113.42", 24) == "203.0.113.0"

    def test_a_slash_zero_erases_the_whole_address(self):
        assert truncate("203.0.113.42", 0) == "0.0.0.0"

    def test_a_bad_octet_is_refused(self):
        with pytest.raises(Invalid):
            truncate("203.0.113.999", 24)

    def test_a_prefix_over_32_is_refused(self):
        with pytest.raises(Invalid):
            truncate("203.0.113.42", 40)


class TestScopedCaching:
    def test_a_global_scope_shares_one_entry(self):
        answer = ScopedAnswer("shop.example.", 24, 0)
        assert answer.is_global()
        assert answer.cache_key("203.0.113.42") == (
            "shop.example.",
            "*",
            0,
        )

    def test_a_scoped_answer_keys_on_the_truncated_subnet(self):
        answer = ScopedAnswer("shop.example.", 24, 24)
        assert answer.cache_key("203.0.113.42") == (
            "shop.example.",
            "203.0.113.0",
            24,
        )

    def test_two_clients_in_one_subnet_share_a_scoped_entry(self):
        answer = ScopedAnswer("shop.example.", 24, 24)
        assert answer.cache_key("203.0.113.5") == answer.cache_key(
            "203.0.113.200"
        )


class TestTheBill:
    def test_a_slash_24_can_split_into_256_entries(self):
        assert entries_under(24, 16) == 256

    def test_a_scope_coarser_than_its_block_cannot_split_it(self):
        with pytest.raises(Invalid) as caught:
            entries_under(16, 24)
        assert "cannot fragment it" in str(caught.value)

    def test_the_report_names_the_fragmentation(self):
        assert "up to 256 distinct cache entries" in (
            fragmentation_report(8)
        )

    def test_a_global_report_promises_no_fragmentation(self):
        assert "no fragmentation" in fragmentation_report(0)
