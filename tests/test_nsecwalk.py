from __future__ import annotations

import pytest

from beacon.errors import Invalid, Loop
from beacon.nsecwalk import leaks_plaintext_names, walk

# a sorted NSEC chain that closes back on the apex
CHAIN = {
    "example.": "mail.example.",
    "mail.example.": "www.example.",
    "www.example.": "example.",
}


class TestWalk:
    def test_the_whole_zone_is_enumerated(self):
        assert walk(CHAIN, "example.") == [
            "example.",
            "mail.example.",
            "www.example.",
        ]

    def test_starting_outside_the_chain_is_refused(self):
        with pytest.raises(Invalid):
            walk(CHAIN, "ghost.example.")

    def test_a_dangling_chain_is_refused(self):
        broken = {"a.": "b.", "b.": "c."}  # c. points nowhere
        with pytest.raises(Invalid):
            walk(broken, "a.")

    def test_an_inner_cycle_is_caught(self):
        # a. -> b. -> c. -> b., a cycle that never returns to a.
        looped = {"a.": "b.", "b.": "c.", "c.": "b."}
        with pytest.raises(Loop):
            walk(looped, "a.")


class TestScheme:
    def test_nsec_leaks_plaintext_names(self):
        assert leaks_plaintext_names("NSEC")

    def test_nsec3_leaks_only_hashes(self):
        assert not leaks_plaintext_names("NSEC3")

    def test_an_unknown_scheme_is_refused(self):
        with pytest.raises(Invalid):
            leaks_plaintext_names("NSEC5")
