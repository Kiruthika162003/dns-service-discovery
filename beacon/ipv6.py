"""IPv6 canonicalization: expand the double-colon shorthand and compress it back one way.

An IPv6 address has two shorthands that make the same address look
different in text, and comparing or keying on the text form requires
canonicalizing them. Leading zeros in each sixteen-bit group may be
dropped, so 0db8 and db8 are the same group, and a single run of
all-zero groups may be replaced by a double colon, so a long stretch
of zeros collapses. The trouble is that the shorthands are ambiguous
in the other direction: the same address has one fully expanded form
but the compression must follow rules to be canonical, replace the
longest run of zero groups, and the first such run when several tie,
or two encoders produce two different strings for one address and a
cache keyed on the text stores it twice. So canonicalizing means
expanding fully to eight four-digit groups, then compressing by that
one deterministic rule, and the result is the single form RFC 5952
prescribes. This matters for AAAA records and for any cache or
comparison over address text. The module expands an address to its
eight full groups, compresses an expanded address by the longest-run
rule, and canonicalizes by doing both, refusing an address with more
than one double colon, which is ambiguous and names no single
address.
"""

from __future__ import annotations

from beacon.errors import Invalid


def expand(addr: str) -> list[str]:
    if addr.count("::") > 1:
        raise Invalid(
            "an address with more than one '::' is ambiguous; it names "
            "no single set of groups"
        )
    if "::" in addr:
        left, right = addr.split("::")
        left_groups = left.split(":") if left else []
        right_groups = right.split(":") if right else []
        missing = 8 - len(left_groups) - len(right_groups)
        if missing < 1:
            raise Invalid("the '::' stands for at least one zero group")
        groups = left_groups + ["0"] * missing + right_groups
    else:
        groups = addr.split(":")
    if len(groups) != 8:
        raise Invalid(f"{addr} does not expand to eight groups")
    return [f"{int(group, 16):04x}" for group in groups]


def compress(groups: list[str]) -> str:
    if len(groups) != 8:
        raise Invalid("compression takes eight expanded groups")
    normalized = [f"{int(group, 16):x}" for group in groups]
    best_start, best_len = -1, 0
    run_start, run_len = -1, 0
    for index, group in enumerate(normalized):
        if group == "0":
            if run_start < 0:
                run_start, run_len = index, 0
            run_len += 1
            if run_len > best_len:
                best_start, best_len = run_start, run_len
        else:
            run_start, run_len = -1, 0
    if best_len < 2:
        return ":".join(normalized)
    head = normalized[:best_start]
    tail = normalized[best_start + best_len :]
    return ":".join(head) + "::" + ":".join(tail)


def canonical(addr: str) -> str:
    return compress(expand(addr))
