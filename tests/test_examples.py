from __future__ import annotations

from examples import (
    discoveryday,
    edgeday,
    firstzone,
    outagenight,
)


class TestEdgeDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert edgeday.main() == 0
        out = capsys.readouterr().out
        assert "big: 60% -> 45%" in out
        assert (
            "the worst failover is eu -> us at 100% of capacity"
        ) in out
        assert "blind spread 28, two-choice spread 3" in out
        assert "kept 1, discarded 1 out-of-district" in out


class TestOutageNight:
    def test_the_night_reads_end_to_end(self, capsys):
        assert outagenight.main() == 0
        out = capsys.readouterr().out
        assert "FAILOVER to us-east" in out
        assert "at +120: 20, the floor" in out
        assert "[STALE, expired 60 tick(s) ago]" in out
        assert "1 refusal(s) avoided, 60 age-tick(s)" in out
        assert "declared steps, not a cliff" in out
        assert "1 query(ies) not sent during backoff" in out
        assert (
            "PRESERVING: 55 renewals against a floor of 85"
        ) in out
        assert (
            "FAILBACK to eu-west after holding recovery 25"
        ) in out
        assert "gone. has nothing even stale" in out


class TestDiscoveryDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert discoveryday.main() == 0
        out = capsys.readouterr().out
        assert "1 of 3 answer; 2 ghost(s) refused" in out
        assert "one bad probe is weather, 3 are climate" in out
        assert (
            "50 client(s) x 4 of 20 backend(s): heaviest "
            "backend seen by 16, lightest by 6"
        ) in out
        assert "big-1: 6 (75%)" in out
        assert "CROSSED ZONES: eu-1 has nobody fit" in out
        assert (
            "no service named anything was ever registered"
        ) in out


class TestFirstZone:
    def test_the_day_reads_end_to_end(self, capsys):
        assert firstzone.main() == 0
        out = capsys.readouterr().out
        assert "www -> 192.0.2.10 (1 upstream)" in out
        assert "blog -> CNAME -> 192.0.2.10" in out
        assert "branch-7.preview -> 192.0.2.99" in out
        assert "second ask from cache = True, 0 upstream" in out
        assert (
            "gone.shop.example. does not exist in shop.example."
        ) in out
        assert "nx2:     remembered = True" in out
        assert "www exists, TXT does not; different no" in out
        assert "5 upstream query(ies) total" in out
        assert "1 negative save(s)" in out
