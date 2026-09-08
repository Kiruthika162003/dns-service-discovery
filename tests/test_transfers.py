from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.names import Name
from beacon.records import Record
from beacon.transfers import TransferPrimary


def a_record(host: str, address: str) -> Record:
    return Record(
        name=Name.parse(f"{host}.example.com"),
        rtype="A",
        value=address,
        ttl=300,
    )


def primary() -> TransferPrimary:
    built = TransferPrimary(serial=100)
    built.publish(101, [a_record("www", "192.0.2.1")], [])
    built.publish(102, [a_record("api", "192.0.2.2")], [])
    return built


class TestPublishing:
    def test_content_moving_without_the_serial_is_refused(self):
        built = primary()
        with pytest.raises(Invalid) as caught:
            built.publish(102, [a_record("x", "192.0.2.9")], [])
        assert "secondaries would sleep through" in str(
            caught.value
        )

    def test_removals_and_additions_both_apply(self):
        built = primary()
        built.publish(
            103,
            [a_record("www", "192.0.2.50")],
            [a_record("www", "192.0.2.1")],
        )
        values = [record.value for record in built.records]
        assert "192.0.2.50" in values
        assert "192.0.2.1" not in values


class TestIncremental:
    def test_a_current_secondary_gets_not_modified(self):
        built = primary()
        status, deltas = built.incremental_transfer(102)
        assert status == "NOT-MODIFIED"
        assert deltas == []
        assert built.not_modified_served == 1

    def test_the_delta_chain_walks_serial_to_serial(self):
        built = primary()
        status, deltas = built.incremental_transfer(100)
        assert status == "DELTAS"
        assert [d.to_serial for d in deltas] == [101, 102]

    def test_falling_off_the_journal_means_ask_for_everything(self):
        built = TransferPrimary(serial=100)
        for step in range(1, 12):
            built.publish(
                100 + step,
                [a_record(f"h{step}", "192.0.2.9")],
                [],
            )
        with pytest.raises(Missing) as caught:
            built.incremental_transfer(100)
        assert "gap dressed as a delta" in str(caught.value)

    def test_the_full_transfer_always_works(self):
        built = primary()
        serial, records = built.full_transfer()
        assert serial == 102
        assert len(records) == 2


class TestTheEconomy:
    def test_the_ledger_prices_the_journal(self):
        built = primary()
        built.incremental_transfer(100)
        built.full_transfer()
        economy = built.economy()
        assert (
            "2 record(s) shipped incrementally, 2 in full"
        ) in economy
        assert "the journal's salary" in economy
