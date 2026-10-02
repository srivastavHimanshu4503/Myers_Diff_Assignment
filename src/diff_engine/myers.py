"""Myers shortest edit script algorithm."""

from collections.abc import Sequence
from typing import TypeVar

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
