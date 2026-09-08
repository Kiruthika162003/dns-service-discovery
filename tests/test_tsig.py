from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.tsig import TsigKey


def key() -> TsigKey:
    return TsigKey(name="transfer.", secret="s3cret", fudge=5)


class TestConstruction:
    def test_a_zero_fudge_is_refused(self):
        with pytest.raises(Refused) as caught:
            TsigKey(name="k.", secret="x", fudge=0)
        assert "a few seconds of honest skew" in str(caught.value)


class TestVerification:
    def test_an_in_window_message_verifies(self):
        assert key().verify("transfer.", 1000, 1003) == "verified"

    def test_a_wrong_key_name_is_badkey(self):
        with pytest.raises(Refused) as caught:
            key().verify("other.", 1000, 1000)
        assert "BADKEY" in str(caught.value)

    def test_a_bad_mac_is_badsig(self):
        with pytest.raises(Refused) as caught:
            key().verify("transfer.", 1000, 1000, mac_matches=False)
        assert "BADSIG" in str(caught.value)

    def test_a_late_replay_is_badtime(self):
        with pytest.raises(Refused) as caught:
            key().verify("transfer.", 1000, 1100)
        assert "BADTIME" in str(caught.value)

    def test_the_edge_of_the_window_still_verifies(self):
        assert key().verify("transfer.", 1000, 1005) == "verified"

    def test_one_second_past_the_edge_is_refused(self):
        with pytest.raises(Refused):
            key().verify("transfer.", 1000, 1006)


class TestPreview:
    def test_would_accept_matches_verify_without_raising(self):
        chosen = key()
        assert chosen.would_accept(1000, 1004)
        assert not chosen.would_accept(1000, 1010)
