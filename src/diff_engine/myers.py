"""Myers shortest edit script algorithm."""

from collections.abc import Sequence
from typing import TypeVar

from diff_engine.models import Edit

T = TypeVar("T")


def _furthest_x(snapshot: list[int], k: int) -> int:
    """Return the furthest x reached on diagonal k during a search round.

    ``snapshot`` holds furthest-x values for diagonals −d, −d+2, …, d where
    d = len(snapshot) − 1.
    """
    d = len(snapshot) - 1
    # k ∈ {−d, −d+2, …, d} step 2, so there are d + 1 elements.
    # Map k to index (k + d) // 2 ∈ [0, d].
    return snapshot[(k + d) // 2]


def _forward_trace(a: Sequence[T], b: Sequence[T]) -> list[list[int]]:
    """Search for the shortest edit path from A to B, saving each round.

    Returns furthest-x snapshots for rounds 0 through D−1, where D is the
    minimum edit distance. The search stops the first time it reaches (N, M),
    ensuring minimality.

    When two predecessor points are equally far, the algorithm prefers the
    DELETE operation (moving right from diagonal k−1) over the INSERT
    operation (moving down from diagonal k+1). This makes deletions appear
    before insertions in the final edit script.
    """
    n, m = len(a), len(b)
    trace: list[list[int]] = []

    for d in range(n + m + 1):
        snapshot: list[int] = []

        for k in range(-d, d + 1, 2):
            # Choose predecessor: down from k+1 (INSERT) or right from k−1 (DELETE).
            if d == 0:
                # Round 0: starting point.
                x = 0
            elif k == -d or (k != d and _furthest_x(trace[-1], k - 1) < _furthest_x(trace[-1], k + 1)):
                # Must come from k+1 (edge case or k+1 is strictly better).
                x = _furthest_x(trace[-1], k + 1)  # down: insert
            else:
                # Come from k−1 (edge case, strictly better, or tie).
                # Tie → this branch → DELETE → deletions appear first.
                x = _furthest_x(trace[-1], k - 1) + 1  # right: delete

            y = x - k

            # Follow matching elements along the diagonal (free moves).
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            # Stop the first time we reach the target.
            if x == n and y == m:
                # The trace does not include the incomplete final round.
                return trace

            snapshot.append(x)

        trace.append(snapshot)

    # Myers' algorithm must reach (N, M) within N + M rounds.
    raise AssertionError("Myers search exceeded N + M rounds")


def _backtrack(trace: list[list[int]], a: Sequence[T], b: Sequence[T]) -> list[Edit[T]]:
    """Reconstruct the minimal edit script by walking the trace backwards.

    Starts at (N, M) and works back to (0, 0), emitting the operations that
    transform A into B. Uses the same tie-breaking rule as the forward search
    so both halves agree on which path was taken.
    """
    n, m = len(a), len(b)
    x, y = n, m
    edits: list[Edit[T]] = []

    # Walk backwards from round D (len(trace)) to round 1.
    # At each step, we're at a point reached during round d+1 and finding
    # the predecessor from round d.
    for d in range(len(trace), 0, -1):
        k = x - y

        # Determine the predecessor using the same rule as the forward search.
        # We look at round d-1's snapshot to find where we came from.
        prev_d = d - 1
        if k == -d or (k != d and _furthest_x(trace[prev_d], k - 1) < _furthest_x(trace[prev_d], k + 1)):
            prev_k = k + 1  # came from k+1 (down: insert)
        else:
            prev_k = k - 1  # came from k-1 (right: delete)

        prev_x = _furthest_x(trace[prev_d], prev_k)
        prev_y = prev_x - prev_k

        # Walk back along the diagonal snake (matching elements).
        while x > prev_x and y > prev_y:
            x -= 1
            y -= 1
            edits.append(Edit("equal", a[x]))

        # Record the single non-diagonal move.
        if x == prev_x:
            # Vertical: insert b[prev_y].
            edits.append(Edit("insert", b[prev_y]))
        else:
            # Horizontal: delete a[prev_x].
            edits.append(Edit("delete", a[prev_x]))

        x, y = prev_x, prev_y

    # Back at (0, 0). If there's a shared prefix, add it.
    while x > 0:
        x -= 1
        y -= 1
        edits.append(Edit("equal", a[x]))

    # Backtracking built the script in reverse.
    edits.reverse()
    return edits


def myers_diff(a: Sequence[T], b: Sequence[T]) -> list[Edit[T]]:
    """Return the minimal edit script transforming A into B.

    The result is a sequence of ``Edit`` operations (equal, insert, delete)
    such that reading the ``equal`` and ``delete`` values reconstructs A,
    and reading the ``equal`` and ``insert`` values reconstructs B.

    When multiple minimal scripts exist, this implementation prefers deletions
    before insertions (the D1 tie-breaking rule confirmed in §44.1).

    Works on any sequences whose elements support ``==``, including strings,
    lists of lines, and lists of characters, making it reusable for both
    line-level and character-level diffs.
    """
    trace = _forward_trace(a, b)
    if not trace:
        # Identical sequences: D = 0, no rounds saved.
        # Return an all-equal script directly.
        return [Edit("equal", item) for item in a]
    return _backtrack(trace, a, b)
