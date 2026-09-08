from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.flagday import resolve_behavior, retries_saved


class TestBehavior:
    def test_a_good_edns_response_is_answered(self):
        assert resolve_behavior("ok", pre_flag_day=True) == "answer"
        assert resolve_behavior("ok", pre_flag_day=False) == "answer"

    def test_before_the_flag_day_silence_triggers_a_retry(self):
        assert (
            resolve_behavior("no-response", pre_flag_day=True)
            == "retry-without-edns"
        )

    def test_after_the_flag_day_silence_is_servfail(self):
        assert (
            resolve_behavior("no-response", pre_flag_day=False)
            == "servfail"
        )

    def test_an_unknown_state_is_refused(self):
        with pytest.raises(Invalid):
            resolve_behavior("shrug", pre_flag_day=False)


class TestRetriesSaved:
    def test_the_flag_day_saves_a_retry_per_broken_server(self):
        assert retries_saved(50, pre_flag_day=False) == 50

    def test_before_the_flag_day_nothing_is_saved(self):
        assert retries_saved(50, pre_flag_day=True) == 0
