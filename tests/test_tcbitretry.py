from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tcbitretry import client_action


class TestAction:
    def test_an_untruncated_udp_answer_is_used(self):
        assert client_action(truncated=False, over_tcp=False) == "use-answer"

    def test_a_truncated_udp_answer_retries_on_tcp(self):
        assert (
            client_action(truncated=True, over_tcp=False)
            == "retry-over-tcp"
        )

    def test_an_untruncated_tcp_answer_is_used(self):
        assert client_action(truncated=False, over_tcp=True) == "use-answer"

    def test_truncation_over_tcp_is_refused(self):
        with pytest.raises(Invalid) as caught:
            client_action(truncated=True, over_tcp=True)
        assert "no size limit to truncate against" in str(caught.value)
