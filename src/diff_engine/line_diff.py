"""Line-level diff: file reading, line splitting, and Myers wrapper."""


class DiffInputError(Exception):
    """Raised when input files cannot be read or decoded."""

    pass


def read_file(path: str) -> str:
    """Read a file as UTF-8 text, strict.

    Raises DiffInputError if the file is missing, unreadable, or contains
    invalid UTF-8. No normalization is applied: CRLF line endings remain as
    ``\\r\\n`` within the text.
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
        return data.decode("utf-8", errors="strict")
    except OSError as e:
        raise DiffInputError(f"Cannot read {path!r}: {e}") from e
    except UnicodeDecodeError as e:
        raise DiffInputError(f"File {path!r} is not valid UTF-8: {e}") from e


def split_lines(text: str) -> tuple[list[str], bool]:
    """Split text into lines, preserving ``\\r`` if present.

    Returns ``(lines, ends_with_newline)``. Lines are split on ``\\n`` only
    (not ``str.splitlines()``, which also splits on ``\\x0b``, ``\\x0c``,
    ``\\u2028``, etc.). A trailing ``\\n`` terminates the last line; it does
    not create an additional empty line.

    Each line includes its content but not the ``\\n`` terminator. A ``\\r``
    before the ``\\n`` remains part of the line, so LF and CRLF line endings
    are observable as different.

    Examples:
        >>> split_lines("")
        ([], False)
        >>> split_lines("a")
        (['a'], False)
        >>> split_lines("a\\n")
        (['a'], True)
        >>> split_lines("a\\r\\n")
        (['a\\r'], True)
        >>> split_lines("\\n")
        ([''], True)
    """
    if not text:
        return ([], False)

    ends_with_newline = text.endswith("\n")
    if ends_with_newline:
        text = text[:-1]  # Remove the final \n; it terminates, doesn't create a line.

    # Split on \n. The empty string after removing a trailing \n splits to [''],
    # which is correct for "\n" -> ([""], True).
    lines = text.split("\n") if text or ends_with_newline else []

    return (lines, ends_with_newline)
