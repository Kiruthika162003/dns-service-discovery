"""Run-length encoding: collapse runs of a repeated value into a value and a count.

Some data is dominated by runs, long stretches of the same value: a
sparse bitmap mostly zeros, a sorted column of repeated keys, a scan
line of one color. Run-length encoding compresses exactly that by
replacing each run with a single pair, the value and how many times
it repeats, so a thousand identical entries become one pair instead
of a thousand entries. Decoding expands the pairs back into the
original sequence, and the two are exact inverses, no information is
lost. The honest caveat is that it is a fit only where runs dominate,
because on data with no runs, where every entry differs from its
neighbor, each value becomes a pair of a value and a count of one, so
the encoding stores two items where there was one and roughly doubles
the size rather than shrinking it. So run-length encoding is not a
general compressor but a specialist that wins big on runny data and
loses on varied data, which is why it is used as a stage inside
larger schemes that first arrange data to have runs. The module
encodes a sequence into value-count pairs, decodes pairs back into
the sequence, and refuses a decode of a non-positive count, which
describes a run that did not occur.
"""

from __future__ import annotations

from beacon.errors import Invalid


def encode(data: list[str]) -> list[tuple[str, int]]:
    runs: list[tuple[str, int]] = []
    for value in data:
        if runs and runs[-1][0] == value:
            last_value, count = runs[-1]
            runs[-1] = (last_value, count + 1)
        else:
            runs.append((value, 1))
    return runs


def decode(runs: list[tuple[str, int]]) -> list[str]:
    result: list[str] = []
    for value, count in runs:
        if count < 1:
            raise Invalid(
                f"a run count of {count} describes a run that did not "
                "occur; counts are positive"
            )
        result.extend([value] * count)
    return result
