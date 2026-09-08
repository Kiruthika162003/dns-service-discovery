from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rrsetorder import harmonize


class TestHarmonize:
    def test_the_set_clamps_to_the_minimum(self):
        result = harmonize([300, 60, 120])
        assert result.ttl == 60

    def test_the_shortened_count_names_the_disagreement(self):
        result = harmonize([300, 60, 120])
        assert result.shortened == 2

    def test_an_agreeing_set_is_untouched(self):
        result = harmonize([90, 90, 90])
        assert result.shortened == 0
        assert "nothing to clamp" in result.report()

    def test_the_report_flags_the_config_bug(self):
        result = harmonize([300, 60])
        assert "config bug to fix at source" in result.report()


class TestRefusals:
    def test_an_empty_set_is_refused(self):
        with pytest.raises(Invalid):
            harmonize([])

    def test_a_negative_ttl_is_refused(self):
        with pytest.raises(Invalid) as caught:
            harmonize([60, -1])
        assert "less than no time" in str(caught.value)
