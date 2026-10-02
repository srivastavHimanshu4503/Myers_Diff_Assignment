"""Independent reference implementations used only by tests.

Nothing here may be imported by ``src/``, and nothing here may reuse the
Myers implementation: these functions exist to check it.
"""

from collections.abc import Iterable, Sequence

from diff_engine.models import Edit


def lcs_length(a: Sequence, b: Sequence) -> int:
    """Length of the longest common subsequence, by dynamic programming.

    Classic O(len(a) * len(b)) table, keeping only the previous row.
    """
    previous = [0] * (len(b) + 1)
    for a_item in a:
        current = [0] * (len(b) + 1)
        for j, b_item in enumerate(b, start=1):
            if a_item == b_item:
                current[j] = previous[j - 1] + 1
            else:
                current[j] = max(previous[j], current[j - 1])
        previous = current
    return previous[-1]


def minimum_edit_distance(a: Sequence, b: Sequence) -> int:
    """True minimum number of insertions + deletions turning A into B.

    Every element of A outside a longest common subsequence must be deleted
    and every element of B outside it must be inserted.
    """
    return len(a) + len(b) - 2 * lcs_length(a, b)


def replay(edits: Iterable[Edit]) -> tuple[list, list]:
    """Rebuild (A, B) from an edit script.

    ``equal`` contributes to both sides, ``delete`` only to A, ``insert``
    only to B. A correct script for (A, B) must replay to exactly (A, B).
    """
    a: list = []
    b: list = []
    for edit in edits:
        if edit.operation == "equal":
            a.append(edit.value)
            b.append(edit.value)
        elif edit.operation == "delete":
            a.append(edit.value)
        else:
            b.append(edit.value)
    return a, b
