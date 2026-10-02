import tempfile
from pathlib import Path

import pytest

from diff_engine.line_diff import DiffInputError, read_file, split_lines


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
