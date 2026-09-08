from __future__ import annotations

import pytest

from beacon.deterministicaperture import aperture_load, spread
from beacon.errors import Invalid


class TestLoad:
    def test_every_backend_is_covered(self):
        counts = aperture_load(num_clients=12, num_backends=6, aperture=2)
        assert all(count > 0 for count in counts)

    def test_the_total_coverage_is_clients_times_aperture(self):
        counts = aperture_load(12, 6, 2)
        assert sum(counts) == 12 * 2


class TestEvenness:
    def test_the_spread_is_small(self):
        # clients a multiple of backends, aperture divides evenly
        assert spread(num_clients=12, num_backends=6, aperture=2) == 0

    def test_even_an_awkward_ratio_stays_tight(self):
        assert spread(num_clients=10, num_backends=6, aperture=2) <= 1


class TestRefusals:
    def test_an_aperture_wider_than_the_ring_is_refused(self):
        with pytest.raises(Invalid):
            aperture_load(10, 6, aperture=7)

    def test_no_backends_is_refused(self):
        with pytest.raises(Invalid):
            aperture_load(10, 0, aperture=1)
