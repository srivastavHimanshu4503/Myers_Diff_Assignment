"""Output rendering for line and character diffs."""

from diff_engine.char_diff import char_ranges
from diff_engine.line_diff import Block
from diff_engine.models import Edit
from diff_engine.pairing import pair_block


def render_line_diff(
    edits: list[Edit[str]],
    a_ends_with_newline: bool,
    b_ends_with_newline: bool,
) -> str:
    """Render line diff with D4 format.

    Prefixes: '  ' (equal), '- ' (delete), '+ ' (insert).
    After the last line from a file that doesn't end with a newline, append
    '\ No newline at end of file' on a separate line.
    """
    if not edits:
        return ""

    lines: list[str] = []
    last_delete_index = None
    last_insert_index = None

    for i, edit in enumerate(edits):
        if edit.operation == "equal":
            lines.append(f"  {edit.value}")
        elif edit.operation == "delete":
            lines.append(f"- {edit.value}")
            last_delete_index = len(lines) - 1
        else:  # insert
            lines.append(f"+ {edit.value}")
            last_insert_index = len(lines) - 1

    # Add "no newline" markers after the last line from each file.
    # Track insertion positions since we're potentially adding two markers.
    markers_to_add: list[tuple[int, str]] = []

    if not a_ends_with_newline and last_delete_index is not None:
        # The last delete line is the last line from file A.
        markers_to_add.append((last_delete_index, r"\ No newline at end of file"))

    if not b_ends_with_newline and last_insert_index is not None:
        # The last insert line is the last line from file B.
        markers_to_add.append((last_insert_index, r"\ No newline at end of file"))

    # Sort by position in reverse so we can insert without shifting indices.
    markers_to_add.sort(key=lambda x: x[0], reverse=True)

    for pos, marker in markers_to_add:
        lines.insert(pos + 1, marker)

    return "\n".join(lines) + "\n"



def _apply_char_markers(line: str, ranges: list[tuple[int, int]], prefix: str) -> str:
    """Apply inline character markers to a line.

    Args:
        line: The line content
        ranges: List of (start, end) character ranges to mark
        prefix: Either "[-" and "-]" for deletes, or "{+" and "+}" for inserts

    Returns:
        Line with inline markers inserted
    """
    if not ranges:
        return line

    # Sort ranges and insert markers from right to left so indices don't shift
    sorted_ranges = sorted(ranges, key=lambda r: r[0], reverse=True)
    
    if prefix == "[-":
        open_marker, close_marker = "[-", "-]"
    else:  # "{+"
        open_marker, close_marker = "{+", "+}"

    result = line
    for start, end in sorted_ranges:
        result = result[:start] + open_marker + result[start:end] + close_marker + result[end:]

    return result


def render_char_diff(
    blocks: list[Block],
    a_ends_with_newline: bool,
    b_ends_with_newline: bool,
) -> str:
    """Render Part B diff with character-level highlighting.

    For paired lines within change blocks, compute character ranges and add
    inline markers (D4: `[-x-]` for deletions, `{+x+}` for insertions).
    Unpaired lines are rendered as whole-line changes without character
    highlights. Equal blocks are rendered as in Part A.

    Uses the same `  ` / `- ` / `+ ` prefixes as Part A.
    """
    if not blocks:
        return ""

    lines: list[str] = []
    last_delete_index = None
    last_insert_index = None

    for block in blocks:
        if block.equal_lines:
            # Equal block: render as Part A
            for line in block.equal_lines:
                lines.append(f"  {line}")
        else:
            # Change block: pair lines and apply character highlighting
            pairs, unpaired_deleted, unpaired_inserted = pair_block(block)

            # Paired lines get character highlights
            for old_line, new_line in pairs:
                deleted_ranges, inserted_ranges = char_ranges(old_line, new_line)
                
                old_with_markers = _apply_char_markers(old_line, deleted_ranges, "[-")
                new_with_markers = _apply_char_markers(new_line, inserted_ranges, "{+")
                
                lines.append(f"- {old_with_markers}")
                last_delete_index = len(lines) - 1
                lines.append(f"+ {new_with_markers}")
                last_insert_index = len(lines) - 1

            # Unpaired lines: render without character highlights
            for line in unpaired_deleted:
                lines.append(f"- {line}")
                last_delete_index = len(lines) - 1

            for line in unpaired_inserted:
                lines.append(f"+ {line}")
                last_insert_index = len(lines) - 1

    # Add "no newline" markers (same logic as Part A)
    markers_to_add: list[tuple[int, str]] = []

    if not a_ends_with_newline and last_delete_index is not None:
        markers_to_add.append((last_delete_index, r"\ No newline at end of file"))

    if not b_ends_with_newline and last_insert_index is not None:
        markers_to_add.append((last_insert_index, r"\ No newline at end of file"))

    markers_to_add.sort(key=lambda x: x[0], reverse=True)

    for pos, marker in markers_to_add:
        lines.insert(pos + 1, marker)

    return "\n".join(lines) + "\n"
