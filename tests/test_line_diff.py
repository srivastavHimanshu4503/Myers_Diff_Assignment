import tempfile
from pathlib import Path

import pytest

from diff_engine.line_diff import DiffInputError, read_file, split_lines, diff_lines, group_edits


# ============================================================================
# split_lines tests
# ============================================================================


@pytest.mark.parametrize(
    ("text", "expected_lines", "expected_eol"),
    [
        # Empty.
        ("", [], False),
        # Single character without newline.
        ("a", ["a"], False),
        # Single character with newline.
        ("a\n", ["a"], True),
        # The edge case: a single newline creates one empty line.
        ("\n", [""], True),
        # Two lines, both with newlines (final newline terminates the last line).
        ("a\n\n", ["a", ""], True),
        # CRLF: \r remains part of the line.
        ("a\r\n", ["a\r"], True),
        # Multiple lines with newlines.
        ("a\nb\n", ["a", "b"], True),
        # Multiple lines, last without newline.
        ("a\nb", ["a", "b"], False),
        # CRLF on multiple lines.
        ("a\r\nb\r\n", ["a\r", "b\r"], True),
        # Mixed LF and CRLF (observable as different).
        ("a\nb\r\n", ["a", "b\r"], True),
        # \x0c is not split (unlike str.splitlines()).
        ("a\x0cb", ["a\x0cb"], False),
        # Unicode.
        ("café\n", ["café"], True),
        ("日本語\n", ["日本語"], True),
    ],
)
def test_split_lines(text, expected_lines, expected_eol):
    lines, eol = split_lines(text)
    assert lines == expected_lines
    assert eol == expected_eol


def test_split_lines_preserves_carriage_return():
    # Explicitly check that \r is not stripped or normalized.
    lines, eol = split_lines("line1\r\nline2\r\n")
    assert lines == ["line1\r", "line2\r"]
    assert eol is True


# ============================================================================
# read_file tests
# ============================================================================


def test_read_file_success():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(b"hello\nworld\n")
        path = f.name
    try:
        content = read_file(path)
        assert content == "hello\nworld\n"
    finally:
        Path(path).unlink()


def test_read_file_preserves_crlf():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(b"line1\r\nline2\r\n")
        path = f.name
    try:
        content = read_file(path)
        assert content == "line1\r\nline2\r\n"
    finally:
        Path(path).unlink()


def test_read_file_unicode():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write("café\n日本語\n".encode("utf-8"))
        path = f.name
    try:
        content = read_file(path)
        assert content == "café\n日本語\n"
    finally:
        Path(path).unlink()


def test_read_file_missing():
    with pytest.raises(DiffInputError, match="Cannot read.*nonexistent"):
        read_file("nonexistent_file_xyz.txt")


def test_read_file_invalid_utf8():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(b"\xff\xfe")  # Invalid UTF-8 sequence
        path = f.name
    try:
        with pytest.raises(DiffInputError, match="not valid UTF-8"):
            read_file(path)
    finally:
        Path(path).unlink()




# ============================================================================
# diff_lines and group_edits tests (P2.2)
# ============================================================================


def test_diff_lines_empty():
    edits = diff_lines([], [])
    assert edits == []


def test_diff_lines_identical():
    a = ["a", "b", "c"]
    b = ["a", "b", "c"]
    edits = diff_lines(a, b)
    assert all(e.operation == "equal" for e in edits)
    assert [e.value for e in edits] == a


def test_diff_lines_spec_section_4_minimality_example():
    # Spec §4: ["a","b","c","d"] vs ["a","b","X","c","d"] should use minimal edits.
    a = ["a", "b", "c", "d"]
    b = ["a", "b", "X", "c", "d"]
    edits = diff_lines(a, b)
    
    # Should be: equal a, equal b, insert X, equal c, equal d (1 insert, no deletes)
    operations = [e.operation for e in edits]
    assert operations.count("delete") == 0
    assert operations.count("insert") == 1
    assert operations.count("equal") == 4


def test_diff_lines_spec_section_15_example():
    # Spec §15: changing "return x * x" to "return x ** 2"
    a = ["def square(x):", "    return x * x"]
    b = ["def square(x):", "    return x ** 2"]
    edits = diff_lines(a, b)
    
    operations = [e.operation for e in edits]
    assert operations == ["equal", "delete", "insert"]


def test_group_edits_empty():
    blocks = group_edits([])
    assert blocks == []


def test_group_edits_all_equal():
    from diff_engine.models import Edit
    edits = [Edit("equal", "a"), Edit("equal", "b"), Edit("equal", "c")]
    blocks = group_edits(edits)
    assert len(blocks) == 1
    assert blocks[0].equal_lines == ["a", "b", "c"]
    assert blocks[0].deleted_lines == []
    assert blocks[0].inserted_lines == []


def test_group_edits_spec_section_4():
    # equal, equal, delete, insert, equal, equal
    from diff_engine.models import Edit
    edits = [
        Edit("equal", "a"),
        Edit("equal", "b"),
        Edit("delete", "c"),
        Edit("insert", "X"),
        Edit("equal", "c"),
        Edit("equal", "d"),
    ]
    blocks = group_edits(edits)
    
    assert len(blocks) == 3
    # Block 0: equal a, b
    assert blocks[0].equal_lines == ["a", "b"]
    assert blocks[0].deleted_lines == []
    assert blocks[0].inserted_lines == []
    # Block 1: delete c, insert X
    assert blocks[1].equal_lines == []
    assert blocks[1].deleted_lines == ["c"]
    assert blocks[1].inserted_lines == ["X"]
    # Block 2: equal c, d
    assert blocks[2].equal_lines == ["c", "d"]
    assert blocks[2].deleted_lines == []
    assert blocks[2].inserted_lines == []


def test_group_edits_adjacent_changes():
    # Two deletes followed by two inserts should form one change block.
    from diff_engine.models import Edit
    edits = [
        Edit("delete", "a"),
        Edit("delete", "b"),
        Edit("insert", "x"),
        Edit("insert", "y"),
    ]
    blocks = group_edits(edits)
    
    assert len(blocks) == 1
    assert blocks[0].equal_lines == []
    assert blocks[0].deleted_lines == ["a", "b"]
    assert blocks[0].inserted_lines == ["x", "y"]


def test_group_edits_separated_changes():
    # change, equal, change should form three blocks.
    from diff_engine.models import Edit
    edits = [
        Edit("delete", "a"),
        Edit("insert", "x"),
        Edit("equal", "b"),
        Edit("delete", "c"),
        Edit("insert", "y"),
    ]
    blocks = group_edits(edits)
    
    assert len(blocks) == 3
    assert blocks[0].deleted_lines == ["a"]
    assert blocks[0].inserted_lines == ["x"]
    assert blocks[1].equal_lines == ["b"]
    assert blocks[2].deleted_lines == ["c"]
    assert blocks[2].inserted_lines == ["y"]
