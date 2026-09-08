from __future__ import annotations

import pytest

from beacon.edns import EdnsNegotiator
from beacon.errors import Invalid


class TestNegotiation:
    def test_a_clean_path_takes_the_big_buffer(self):
        neg = EdnsNegotiator()
        verdict = neg.negotiate(path_mtu=9000, name="www.")
        assert "negotiated 4096-byte buffer on the first try" in (
            verdict
        )

    def test_a_middlebox_forces_a_smaller_buffer(self):
        neg = EdnsNegotiator()
        verdict = neg.negotiate(path_mtu=1400, name="www.")
        assert "4096 was swallowed, 1232 got through" in verdict
        assert "not a dead name" in verdict
        assert neg.false_negatives_avoided == 1

    def test_the_silence_is_never_read_as_nxdomain(self):
        neg = EdnsNegotiator()
        verdict = neg.negotiate(path_mtu=700, name="www.")
        assert "torn envelope, not a dead name" in verdict

    def test_the_tiny_path_forces_tcp(self):
        neg = EdnsNegotiator()
        verdict = neg.negotiate(path_mtu=511, name="www.")
        assert "forcing TCP" in verdict

    def test_a_sub_udp_path_forces_tcp_not_a_refusal(self):
        neg = EdnsNegotiator()
        verdict = neg.negotiate(path_mtu=400, name="x.")
        assert "forcing TCP" in verdict
        assert neg.forced_tcp == 1

    def test_a_capacityless_path_is_refused(self):
        with pytest.raises(Invalid):
            EdnsNegotiator().negotiate(path_mtu=0, name="x.")


class TestThePathMap:
    def test_the_map_is_discovered_by_traffic(self):
        neg = EdnsNegotiator()
        neg.negotiate(path_mtu=9000, name="a.")
        neg.negotiate(path_mtu=1400, name="b.")
        neg.negotiate(path_mtu=1400, name="c.")
        report = neg.path_mtu_map()
        assert "4096 bytes: 1 time(s)" in report
        assert "1232 bytes: 2 time(s)" in report
        assert "2 false negative(s) avoided" in report

    def test_no_negotiations_no_map(self):
        with pytest.raises(Invalid):
            EdnsNegotiator().path_mtu_map()
