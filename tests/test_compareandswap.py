from __future__ import annotations

from beacon.compareandswap import AtomicCell


class TestCas:
    def test_a_matching_expectation_swaps(self):
        cell = AtomicCell("A")
        assert cell.cas("A", "B")
        assert cell.value == "B"

    def test_a_mismatched_expectation_fails(self):
        cell = AtomicCell("A")
        assert not cell.cas("Z", "B")
        assert cell.value == "A"


class TestABA:
    def test_plain_cas_is_fooled_by_a_value_that_came_back(self):
        cell = AtomicCell("A")
        # a reader captures expected "A", then the value goes A->B->A
        cell.cas("A", "B")
        cell.cas("B", "A")
        # the stale reader's CAS on "A" wrongly succeeds
        assert cell.cas("A", "C")

    def test_stamped_cas_catches_the_intervening_change(self):
        cell = AtomicCell("A")
        reader_stamp = cell.stamp  # captured before the ABA churn
        cell.cas("A", "B")
        cell.cas("B", "A")
        # value is "A" again but the stamp advanced, so the stale
        # stamped CAS correctly fails
        assert not cell.stamped_cas("A", reader_stamp, "C")

    def test_a_current_stamped_cas_succeeds(self):
        cell = AtomicCell("A")
        assert cell.stamped_cas("A", cell.stamp, "B")
