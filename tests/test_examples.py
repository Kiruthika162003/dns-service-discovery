from __future__ import annotations

from examples import firstzone


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
