"""Command-line interface for the diff engine."""

import argparse
import sys

from diff_engine.line_diff import DiffInputError, diff_lines, group_edits, read_file, split_lines
from diff_engine.renderer import render_char_diff, render_line_diff


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Returns:
        0 if files are identical, 1 if differences exist, 2 on error.
    """
    parser = argparse.ArgumentParser(
        prog="diff_engine",
        description="Myers shortest-edit-script diff engine with line and character diffs",
    )
    parser.add_argument(
        "--part",
        choices=["A", "B"],
        default="B",
        help="Part A (line diff only) or Part B (line + character diff, default)",
    )
    parser.add_argument("file_a", metavar="FILE_A", help="Original file")
    parser.add_argument("file_b", metavar="FILE_B", help="Modified file")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit on error; capture it for testability
        return 2 if e.code != 0 else 0

    # Read files
    try:
        a_text = read_file(args.file_a)
        b_text = read_file(args.file_b)
    except DiffInputError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    # Split into lines
    a_lines, a_eol = split_lines(a_text)
    b_lines, b_eol = split_lines(b_text)

    # Compute diff
    edits = diff_lines(a_lines, b_lines)

    # Check if files are identical
    if all(e.operation == "equal" for e in edits):
        return 0

    # Render output
    if args.part == "A":
        output = render_line_diff(edits, a_eol, b_eol)
    else:  # Part B
        blocks = group_edits(edits)
        output = render_char_diff(blocks, a_eol, b_eol)

    print(output, end="")
    return 1
