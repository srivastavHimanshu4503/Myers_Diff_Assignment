"""Character-level diff for changed line pairs."""

from diff_engine.myers import myers_diff


def char_ranges(old: str, new: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Compute changed character ranges within a pair of lines.

    Uses Myers diff on characters, then merges consecutive non-equal characters
    into half-open (start, end) ranges. Returns (deleted_ranges, inserted_ranges)
    where each range is a tuple of (start_index, end_index) into the respective
    string.

    The ranges identify which characters differ. An invariant: removing the
    deleted ranges from ``old`` and the inserted ranges from ``new`` should
    yield the same common string.

    Examples:
        >>> char_ranges("8000", "8080")
        ([(2, 3)], [(2, 3)])  # Position 2: '0' vs '8'
        
        >>> char_ranges("abc", "abc")
        ([], [])  # Identical
        
        >>> char_ranges("abc", "xyz")
        ([(0, 3)], [(0, 3)])  # Fully different
    """
    edits = myers_diff(old, new)

    deleted_ranges: list[tuple[int, int]] = []
    inserted_ranges: list[tuple[int, int]] = []

    old_pos = 0
    new_pos = 0
    delete_start = None
    insert_start = None

    for edit in edits:
        if edit.operation == "equal":
            # Finalize any open ranges.
            if delete_start is not None:
                deleted_ranges.append((delete_start, old_pos))
                delete_start = None
            if insert_start is not None:
                inserted_ranges.append((insert_start, new_pos))
                insert_start = None
            old_pos += 1
            new_pos += 1
        elif edit.operation == "delete":
            if delete_start is None:
                delete_start = old_pos
            old_pos += 1
        else:  # insert
            if insert_start is None:
                insert_start = new_pos
            new_pos += 1

    # Finalize any ranges still open at the end.
    if delete_start is not None:
        deleted_ranges.append((delete_start, old_pos))
    if insert_start is not None:
        inserted_ranges.append((insert_start, new_pos))

    return (deleted_ranges, inserted_ranges)
