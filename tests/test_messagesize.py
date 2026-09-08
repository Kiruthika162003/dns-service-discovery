from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.messagesize import (
    fragmentation_risk,
    needs_truncation,
    negotiated_size,
)


class TestNegotiation:
    def test_no_edns_falls_to_the_512_floor(self):
        assert negotiated_size(None, server_max=4096) == 512

    def test_the_smaller_of_client_and_server_wins(self):
        assert negotiated_size(1232, server_max=4096) == 1232
        assert negotiated_size(4096, server_max=1400) == 1400

    def test_the_512_floor_holds_against_a_tiny_advertisement(self):
        assert negotiated_size(200, server_max=4096) == 512

    def test_a_server_max_below_the_floor_is_refused(self):
        with pytest.raises(Invalid):
            negotiated_size(1232, server_max=400)


class TestTruncation:
    def test_a_fitting_answer_is_not_truncated(self):
        assert not needs_truncation(800, 1232)

    def test_an_oversize_answer_is_truncated(self):
        assert needs_truncation(2000, 1232)


class TestFragmentation:
    def test_a_large_advertisement_risks_fragmentation(self):
        assert fragmentation_risk(4096)

    def test_the_recommended_size_does_not(self):
        assert not fragmentation_risk(1232)
