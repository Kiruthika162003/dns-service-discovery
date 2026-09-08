from __future__ import annotations

from examples import (
    concurrencyday,
    consensusday,
    convergenceday,
    discoveryday,
    edgeday,
    electionday,
    firstzone,
    outagenight,
    resilienceday,
    secureday,
    storageday,
)


class TestSecureDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert secureday.main() == 0
        out = capsys.readouterr().out
        assert (
            "trust chain intact through 3 zone(s) to the "
            "trusted root ."
        ) in out
        assert "STALE LINK: shop.com. rotated its key" in out
        assert (
            "old key retired; no cache holds a signature it "
            "cannot check"
        ) in out
        assert "a safe rollover at ttl 30 takes at least 60" in (
            out
        )
        assert (
            "traditionally 4 server(s) learned the full name, "
            "minimization leaves 1"
        ) in out
        assert (
            "6 distinct length(s) collapse to 3, spending 306"
        ) in out


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


class TestConsensusDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert consensusday.main() == 0
        out = capsys.readouterr().out
        assert "prevote: 3 grants, election allowed = True" in out
        assert "vote granted = True in term 5" in out
        assert "follower log [1, 1, 2] -> [1, 1, 3, 3]" in out
        assert "index advances to 6 on a majority" in out
        assert "linearizable read: serve" in out
        assert "joint majority across old and new = True" in out
        assert "send-timeout-now to a caught-up successor" in out
        assert "leadership is not freshly confirmed" in out


class TestResilienceDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert resilienceday.main() == 0
        out = capsys.readouterr().out
        assert "breaker open blocks = True, probe at cooldown = True" in out
        assert "fixed 3x loads 3000, budget loads 1210" in out
        assert "hedge fires on 5%, tail 125ms" in out
        assert "the shed order is ['low', 'normal', 'high']" in out
        assert "db saturated, cache still open: ['db']" in out
        assert "2 of 10 healthy: panic routes to all 10" in out
        assert "ghost has no compartment" in out


class TestConvergenceDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert convergenceday.main() == 0
        out = capsys.readouterr().out
        assert "version vectors say: concurrent" in out
        assert "PN-counter converges to 12 either merge order" in out
        assert "add-wins over concurrent remove = True" in out
        assert "merkle found ['k100'] in 17 comparisons of 256" in out
        assert "read repair keeps new v5, repairs ['r1', 'r3']" in out
        assert "sends only the deltas the peer lacks: ['n2']" in out
        assert "no newest version to repair toward" in out


class TestStorageDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert storageday.main() == 0
        out = capsys.readouterr().out
        assert "crash replays ['set b=2']" in out
        assert "third write says flush-due" in out
        assert "write amp 40, read amp 4" in out
        assert "30s tombstone risks resurrection = True" in out
        assert "replays 6000 records" in out
        assert "cannot apply to index 5" in out


class TestConcurrencyDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert concurrencyday.main() == 0
        out = capsys.readouterr().out
        assert "the race loser aborted; value stays from-a" in out
        assert "shared+shared = True, shared+exclusive = False" in out
        assert "deadlock = True, cycle ['t1', 't2', 't3']" in out
        assert "older requester -> wait, younger requester -> die" in out
        assert "a snapshot at 15 reads v1" in out
        assert "two transactions share a timestamp" in out


class TestElectionDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert electionday.main() == 0
        out = capsys.readouterr().out
        assert "no higher node -> win" in out
        assert "leader of [2,7,4] is 7" in out
        assert "ring election of [3,7,1,5] elects 7" in out
        assert "an epoch-0 op after the bump is fenced = True" in out
        assert "the ring has duplicate ids" in out


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
