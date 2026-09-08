"""Resuming a watch: incremental while the history covers you, a full resync once it does not.

A client watching a registry for changes streams them from a
resource version, a monotonic marker, and after a disconnect it
resumes by asking for everything since the version it last saw. That
works only while the server still retains the history back to that
version, and retention is finite: the server compacts old change
records to bound memory, so a client that was gone long enough finds
its version has fallen off the back of the retained window. When
that happens the server cannot send the missed changes because they
no longer exist, and the honest response is not to fail but to tell
the client to resync, to list the full current state and start a
fresh watch from the newest version, accepting the cost of a
complete read rather than pretend an incremental catch-up is
possible. This is the same shape as a zone transfer dropping IXFR
for AXFR, and a Raft follower needing a snapshot install: an
incremental path bounded by a retention window, with a full-state
fallback for whoever fell outside it. The module decides resume,
resync, or refusal from where the client's version sits relative to
the retained window and the current version.
"""

from __future__ import annotations

from beacon.errors import Invalid, Lagging


def resume_plan(
    client_version: int, oldest_retained: int, current_version: int
) -> str:
    if client_version > current_version:
        raise Invalid(
            f"the client's version {client_version} is ahead of the "
            f"server's {current_version}; a watcher cannot have seen "
            "the future"
        )
    if client_version < oldest_retained:
        raise Lagging(
            f"version {client_version} fell off the retained window "
            f"(oldest {oldest_retained}); the missed changes are "
            "compacted away, so a full resync is required"
        )
    return "resume-incremental"
