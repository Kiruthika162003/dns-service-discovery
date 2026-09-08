from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.negativettl import negative_ttl, over_caches_new_names


class TestNegativeTtl:
    def test_it_takes_the_minimum_of_the_two(self):
        assert negative_ttl(soa_ttl=3600, soa_minimum=300) == 300
        assert negative_ttl(soa_ttl=300, soa_minimum=3600) == 300

    def test_equal_fields_return_that_value(self):
        assert negative_ttl(600, 600) == 600

    def test_a_negative_field_is_refused(self):
        with pytest.raises(Invalid):
            negative_ttl(-1, 300)


class TestOverCaching:
    def test_a_long_negative_ttl_hides_new_names(self):
        # negative ttl 3600 exceeds a refresh of 900
        assert over_caches_new_names(3600, 7200, refresh=900)

    def test_a_short_negative_ttl_does_not(self):
        assert not over_caches_new_names(300, 300, refresh=900)
