import pytest

from diff_engine.char_diff import char_ranges


def test_char_ranges_spec_example_8000_to_8080():
    # Spec §17: changing "8000" to "8080"
    # Myers finds: equal '8', equal '0', insert '8', equal '0', delete '0'
    # So deleted range is at position 3, inserted range at position 2
    deleted, inserted = char_ranges("8000", "8080")
    assert deleted == [(3, 4)]
    assert inserted == [(2, 3)]


def test_char_ranges_identical():
    deleted, inserted = char_ranges("same", "same")
    assert deleted == []
    assert inserted == []


def test_char_ranges_empty_to_nonempty():
    deleted, inserted = char_ranges("", "abc")
    assert deleted == []
    assert inserted == [(0, 3)]


def test_char_ranges_nonempty_to_empty():
    deleted, inserted = char_ranges("abc", "")
    assert deleted == [(0, 3)]
    assert inserted == []


def test_char_ranges_fully_different():
    deleted, inserted = char_ranges("abc", "xyz")
    assert deleted == [(0, 3)]
    assert inserted == [(0, 3)]


def test_char_ranges_multiple_separated_changes():
    # "a_b_c" -> "x_y_z": positions 0, 2, 4 differ
    deleted, inserted = char_ranges("a_b_c", "x_y_z")
    # Consecutive non-equal chars merge, separated by equal chars split
    assert deleted == [(0, 1), (2, 3), (4, 5)]
    assert inserted == [(0, 1), (2, 3), (4, 5)]


def test_char_ranges_long_line():
    # 2000-char line with one change at position 1000
    old = "a" * 1000 + "X" + "b" * 999
    new = "a" * 1000 + "Y" + "b" * 999
    deleted, inserted = char_ranges(old, new)
    assert deleted == [(1000, 1001)]
    assert inserted == [(1000, 1001)]


def test_char_ranges_unicode():
    # Unicode characters
    deleted, inserted = char_ranges("café", "cafe")
    # 'é' vs 'e' at position 3
    assert deleted == [(3, 4)]
    assert inserted == [(3, 4)]


def test_char_ranges_unicode_emoji():
    deleted, inserted = char_ranges("emoji😀", "emoji🎉")
    # Emoji differ at position 5
    assert deleted == [(5, 6)]
    assert inserted == [(5, 6)]


def test_char_ranges_invariant_common_string():
    """Removing changed ranges from both strings yields the same common string."""
    old = "timeout = 8000"
    new = "timeout = 8080"
    deleted_ranges, inserted_ranges = char_ranges(old, new)

    # Remove deleted ranges from old
    old_parts = []
    prev = 0
    for start, end in deleted_ranges:
        old_parts.append(old[prev:start])
        prev = end
    old_parts.append(old[prev:])
    old_common = "".join(old_parts)

    # Remove inserted ranges from new
    new_parts = []
    prev = 0
    for start, end in inserted_ranges:
        new_parts.append(new[prev:start])
        prev = end
    new_parts.append(new[prev:])
    new_common = "".join(new_parts)

    assert old_common == new_common
