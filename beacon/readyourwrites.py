"""Read-your-writes: a client's own reads always reflect its own writes.

The most jarring inconsistency a user meets is saving something and
then not seeing it: the write went to one replica, the following
read landed on another that had not yet received it, and the record
appears unchanged, as if the save were lost. Read-your-writes is the
session guarantee that removes exactly that surprise. The session
remembers the version the client's last write produced, and a
replica may serve the client's subsequent reads only if it has
caught up to that version, so a client always sees at least its own
most recent write, whatever else it may or may not see. Like the
other session guarantees this is scoped to one client, so it does
not promise the client sees other clients' latest writes, only its
own, which is what makes it far cheaper than global strong
consistency while still eliminating the lost-update illusion. The
enforcement is the same shape: steer the read to a replica that has
the client's write, or wait for one to. The module tracks the
version of the client's last write and decides whether a replica is
current enough to serve that client without hiding its own change.
"""

from __future__ import annotations


def acceptable(last_write_version: int, replica_version: int) -> bool:
    return replica_version >= last_write_version


def record_write(last_write_version: int, new_write_version: int) -> int:
    return max(last_write_version, new_write_version)
