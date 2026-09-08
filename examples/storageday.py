"""The storage day: a write survives a crash, buffers to a sorted flush, and a delete stays dead.

Run with: python -m examples.storageday
"""

from __future__ import annotations

from beacon.checkpointing import replay_work
from beacon.lsmcompaction import read_amplification, write_amplification
from beacon.memtable import MemTable
from beacon.tombstonegc import may_collect, resurrection_risk_if_collected
from beacon.wal import WriteAheadLog


def morning_the_log():
    wal = WriteAheadLog()
    wal.append("set a=1")
    wal.append("set b=2")
    wal.apply_up_to(1)
    print(f"morning  crash replays {wal.replay()} (a=1 was persisted)")


def midday_the_memtable():
    table = MemTable(threshold=3)
    for key, value in (("c", "3"), ("a", "1"), ("b", "2")):
        verdict = table.put(key, value)
    print(f"midday   third write says {verdict}, flush = {table.flush()}")


def afternoon_the_amplification():
    print(
        f"afternoon leveled compaction: write amp "
        f"{write_amplification(4, 10)}, read amp {read_amplification(4)}"
    )


def evening_the_tombstone():
    early = resurrection_risk_if_collected(30, grace_period=60)
    late = may_collect(100, grace_period=60)
    print(
        f"evening  collecting a 30s tombstone risks resurrection = {early}; "
        f"a 100s one is collectible = {late}"
    )


def night_the_checkpoint():
    print(
        f"night    a 60s checkpoint interval at 100 writes/s replays "
        f"{replay_work(60, 100):.0f} records after a crash"
    )


def main() -> int:
    morning_the_log()
    midday_the_memtable()
    afternoon_the_amplification()
    evening_the_tombstone()
    night_the_checkpoint()
    try:
        WriteAheadLog().apply_up_to(5)
    except Exception as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
