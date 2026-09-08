from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.unknownrr import is_known, may_compress_rdata, render


class TestClassification:
    def test_a_known_type_is_known(self):
        assert is_known(1)  # A
        assert is_known(28)  # AAAA

    def test_an_unknown_type_is_opaque(self):
        assert not is_known(9999)


class TestRendering:
    def test_a_known_type_renders_as_parsed(self):
        assert render(1, b"\xc0\x00\x02\x01") == "A (parsed)"

    def test_an_unknown_type_renders_generic(self):
        result = render(9999, b"\xde\xad")
        assert result == r"TYPE9999 \# 2 dead"

    def test_a_negative_type_is_refused(self):
        with pytest.raises(Invalid):
            render(-1, b"")


class TestCompressionSafety:
    def test_known_rdata_may_be_compressed(self):
        assert may_compress_rdata(2)  # NS holds a name

    def test_unknown_rdata_is_never_compressed(self):
        assert not may_compress_rdata(9999)
