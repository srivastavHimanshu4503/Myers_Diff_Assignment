"""Changed-line pairing for character-level diff."""

from diff_engine.line_diff import Block


def pair_block(block: Block) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """Pair deleted and inserted lines within a change block.

    Uses positional pairing (D3): the i-th deleted line pairs with the i-th
    inserted line. Surplus lines remain unpaired and are rendered without
    character highlights.

    Returns:
        (pairs, unpaired_deleted, unpaired_inserted)
        where pairs is a list of (deleted_line, inserted_line) tuples.
    """
    deleted = block.deleted_lines
    inserted = block.inserted_lines

    n_pairs = min(len(deleted), len(inserted))
    pairs = [(deleted[i], inserted[i]) for i in range(n_pairs)]
    unpaired_deleted = deleted[n_pairs:]
    unpaired_inserted = inserted[n_pairs:]

    return (pairs, unpaired_deleted, unpaired_inserted)
