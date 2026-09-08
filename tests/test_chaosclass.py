from __future__ import annotations

import pytest

from beacon.chaosclass import answer, leaks_fingerprint
from beacon.errors import Invalid

VALUES = {
    "version.bind.": "beacon 9.18.1",
    "id.server.": "anycast-fra-3",
}


class TestDisclosure:
    def test_a_disclosed_name_returns_its_value(self):
        assert (
            answer("id.server.", {"id.server."}, VALUES)
            == "anycast-fra-3"
        )

    def test_an_undisclosed_name_is_obfuscated(self):
        assert (
            answer("version.bind.", set(), VALUES) == "not disclosed"
        )

    def test_a_non_chaos_name_is_refused(self):
        with pytest.raises(Invalid) as caught:
            answer("www.example.", {"www.example."}, VALUES)
        assert "not a known CHAOS name" in str(caught.value)


class TestFingerprint:
    def test_disclosing_the_version_leaks_a_fingerprint(self):
        assert leaks_fingerprint("version.bind.", {"version.bind."})

    def test_hiding_the_version_does_not(self):
        assert not leaks_fingerprint("version.bind.", set())

    def test_the_server_id_is_not_a_fingerprint(self):
        assert not leaks_fingerprint("id.server.", {"id.server."})
