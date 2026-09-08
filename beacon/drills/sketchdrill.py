"""Count-min never undercounts, even buried under collisions from a noisy stream.

The count-min sketch's whole value rests on its estimate being at
least the true count, so a heavy hitter is never hidden, and the
drill stresses exactly that against collision noise. It counts one
name fifty times, then floods the sketch with five hundred distinct
cold names to force collisions into the heavy name's cells, and
holds that the estimate is still at least fifty and still strictly
above a once-seen name's estimate. If collisions could ever drag an
estimate below the truth the sketch would be useless for its one
job, so the drill pins the never-undercount direction under the
noise that would expose a broken minimum.
"""

from __future__ import annotations

from beacon.countminsketch import CountMinSketch
from beacon.drills.finding import Finding


def run() -> Finding:
    sketch = CountMinSketch(width=64, depth=4)
    for _ in range(50):
        sketch.add("heavy")
    for i in range(500):
        sketch.add(f"cold-{i}")
    sketch.add("light")
    heavy = sketch.estimate("heavy")
    light = sketch.estimate("light")
    numbers = {
        "heavy_estimate": heavy,
        "at_least_truth": heavy >= 50,
        "light_estimate": light,
        "heavy_beats_light": heavy > light,
    }
    holds = heavy >= 50 and heavy > light
    return Finding(
        drill="countmin",
        claim=(
            "after 500 colliding cold names the heavy count still "
            "estimates at least its true 50 and still beats a "
            "once-seen name, so collisions never drag it below truth"
        ),
        numbers=numbers,
        holds=holds,
    )
