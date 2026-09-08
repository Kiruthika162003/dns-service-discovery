from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.sloppyquorum import (
    has_consistency_window,
    needed_substitutes,
    sloppy_succeeds,
    strict_succeeds,
)


class TestStrict:
    def test_enough_home_acks_succeed(self):
        assert strict_succeeds(home_acks=2, w=2)

    def test_too_few_home_acks_fail(self):
        assert not strict_succeeds(home_acks=1, w=2)

    def test_a_zero_quorum_is_refused(self):
        with pytest.raises(Invalid):
            strict_succeeds(1, w=0)


class TestSloppy:
    def test_substitutes_make_up_the_shortfall(self):
        # only 1 home ack, but a substitute brings it to 2
        assert sloppy_succeeds(home_acks=1, substitute_acks=1, w=2)

    def test_still_short_even_with_substitutes_fails(self):
        assert not sloppy_succeeds(home_acks=1, substitute_acks=0, w=3)


class TestReporting:
    def test_the_shortfall_names_the_substitutes_needed(self):
        assert needed_substitutes(home_acks=1, w=3) == 2

    def test_no_shortfall_needs_no_substitutes(self):
        assert needed_substitutes(home_acks=3, w=3) == 0

    def test_a_sloppy_write_has_a_consistency_window(self):
        assert has_consistency_window(home_acks=1, w=2)
        assert not has_consistency_window(home_acks=2, w=2)
