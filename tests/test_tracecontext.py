from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tracecontext import child, is_sampled, parse

PARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


class TestParse:
    def test_it_splits_the_fields(self):
        trace_id, span_id, flags = parse(PARENT)
        assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert span_id == "00f067aa0ba902b7"
        assert flags == "01"

    def test_a_malformed_header_is_refused(self):
        with pytest.raises(Invalid):
            parse("not-a-traceparent")

    def test_an_all_zero_trace_id_is_refused(self):
        with pytest.raises(Invalid):
            parse(f"00-{'0' * 32}-00f067aa0ba902b7-01")


class TestSampled:
    def test_the_low_bit_is_the_sampled_flag(self):
        assert is_sampled("01")
        assert not is_sampled("00")


class TestChild:
    def test_a_child_keeps_the_trace_id_and_flags(self):
        new = child(PARENT, "b7ad6b7169203331")
        trace_id, span_id, flags = parse(new)
        assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert span_id == "b7ad6b7169203331"
        assert flags == "01"  # sampled flag propagated unchanged

    def test_a_bad_span_id_is_refused(self):
        with pytest.raises(Invalid):
            child(PARENT, "short")
