"""A process-wide Python recursion limit that's safe to raise from several threads.

The compiler recurses once per nesting level (the parser, the type checker, the
code generator and the interpreter), so deep programs need more than Python's
default 1,000 frames. ``sys.setrecursionlimit`` is global to the interpreter,
not per thread, and servers run several programs at once. So the limit is
shared: raised while any run needs it, and restored when the last one finishes.
(Saving and restoring it per run would let overlapping runs "restore" each
other's raised value forever.)
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager

# The parser caps nesting (parser.MAX_NESTING) at a depth that fits in this limit
# (about 14 Python frames per level in the parser).
FRONT_END_RECURSION_LIMIT = 10_000

_recursion_lock = threading.Lock()
_active_minimums: list[int] = []
_original_limit: int | None = None


def _apply_recursion_limit() -> None:
    target = max(_active_minimums, default=0)
    assert _original_limit is not None
    sys.setrecursionlimit(max(_original_limit, target))


@contextmanager
def python_recursion_limit(minimum: int) -> Iterator[None]:
    global _original_limit
    with _recursion_lock:
        if not _active_minimums:
            _original_limit = sys.getrecursionlimit()
        _active_minimums.append(minimum)
        _apply_recursion_limit()
    try:
        yield
    finally:
        with _recursion_lock:
            _active_minimums.remove(minimum)
            _apply_recursion_limit()
            if not _active_minimums:
                _original_limit = None
