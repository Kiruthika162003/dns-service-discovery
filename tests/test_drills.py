from __future__ import annotations

from beacon.cli import main
from beacon.drills import registry


class TestTheRegistry:
    def test_every_drill_holds(self):
        assert registry.broken() == []

    def test_the_report_ends_with_the_tally(self):
        report = registry.report()
        assert report.splitlines()[-1] == "2 drills, 0 broken"

    def test_findings_carry_their_numbers(self):
        for finding in registry.all_findings():
            assert finding.numbers
            assert finding.claim


class TestTheCli:
    def test_summary_is_one_line(self, capsys):
        assert main(["summary"]) == 0
        assert capsys.readouterr().out.strip() == (
            "2 drills (0 broken)"
        )

    def test_check_says_all_hold(self, capsys):
        assert main(["check"]) == 0
        assert "all drills hold" in capsys.readouterr().out

    def test_drills_prints_the_page(self, capsys):
        assert main(["drills"]) == 0
        out = capsys.readouterr().out
        assert "[holds] deadnames:" in out
