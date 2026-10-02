"""Output rendering for line and character diffs."""

from diff_engine.models import Edit


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
