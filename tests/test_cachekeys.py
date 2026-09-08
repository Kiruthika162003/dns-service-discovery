from __future__ import annotations

import pytest

from beacon.cachekeys import cache_key, canonical, same_entry
from beacon.errors import Invalid


class TestCanonical:
    def test_case_is_folded(self):
        assert canonical("www.Example.COM") == "www.example.com."

    def test_the_root_dot_is_added(self):
        assert canonical("example.com") == "example.com."

    def test_an_already_rooted_name_is_unchanged(self):
        assert canonical("example.com.") == "example.com."

    def test_an_empty_name_is_refused(self):
        with pytest.raises(Invalid):
            canonical("")


class TestKey:
    def test_the_key_folds_name_and_upcases_type(self):
        assert cache_key("WWW.example.com", "a") == (
            "www.example.com.",
            "A",
            "IN",
        )

    def test_the_0x20_varied_queries_share_one_entry(self):
        assert same_entry(
            ("www.example.com", "A"), ("WwW.ExAmPlE.CoM.", "A")
        )

    def test_different_types_do_not_collide(self):
        assert not same_entry(
            ("www.example.com", "A"), ("www.example.com", "MX")
        )
