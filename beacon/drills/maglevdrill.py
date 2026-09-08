"""Maglev's two promises, evenness and minimal churn, measured on one table at once.

The build makes two claims that pull against intuition together:
that a table filled by a turn-taking permutation is close to
even, and that dropping a backend and rebuilding stirs only a
small fraction of keys. A drill that checked one without the
other could pass while the algorithm was quietly broken, an even
table that reshuffled everything on a change, or a stable table
that had piled load on one backend, so this drill holds both at
once over a real table and a real removal. The numbers it fixes,
a spread within two slots and under forty percent of three
thousand keys moved when one of five backends leaves, are the
bounds a correct build stays inside and a subtle bug pushes past.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.maglev import MaglevTable, disruption

KEYS = [f"key-{i}" for i in range(3000)]


def run() -> Finding:
    before = MaglevTable(["b0", "b1", "b2", "b3", "b4"], size=97)
    after = MaglevTable(["b0", "b1", "b2", "b3"], size=97)
    fraction = disruption(before, after, KEYS)
    spread = before.spread()
    numbers = {
        "spread_slots": spread,
        "disruption": round(fraction, 3),
        "even_within_two": spread <= 2,
        "moved_under_40pct": fraction < 0.40,
    }
    holds = spread <= 2 and fraction < 0.40
    return Finding(
        drill="maglev",
        claim=(
            "a 97-slot Maglev table over five backends spreads "
            "within two slots and, dropping one backend, moves "
            "under 40% of 3000 keys, holding evenness and minimal "
            "churn at the same time"
        ),
        numbers=numbers,
        holds=holds,
    )
