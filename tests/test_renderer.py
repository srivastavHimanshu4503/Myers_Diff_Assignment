import pytest

from diff_engine.models import Edit
from diff_engine.renderer import render_line_diff


def test_render_line_diff_empty():
    result = render_line_diff([], True, True)
    assert result == ""


def test_render_line_diff_all_equal():
    edits = [
        Edit("equal", "a"),
        Edit("equal", "b"),
        Edit("equal", "c"),
    ]
    result = render_line_diff(edits, True, True)
    assert result == "  a\n  b\n  c\n"


def test_render_line_diff_spec_section_15():
    # Spec §15: "def square(x):" equal, line changed
    edits = [
        Edit("equal", "def square(x):"),
        Edit("delete", "    return x * x"),
        Edit("insert", "    return x ** 2"),
    ]
    result = render_line_diff(edits, True, True)
    expected = (
        "  def square(x):\n"
        "-     return x * x\n"
        "+     return x ** 2\n"
    )
    assert result == expected


def test_render_line_diff_missing_newline_in_a_only():
    edits = [
        Edit("equal", "line1"),
        Edit("delete", "old"),
    ]
    result = render_line_diff(edits, a_ends_with_newline=False, b_ends_with_newline=True)
    expected = (
        "  line1\n"
        "- old\n"
        r"\ No newline at end of file" + "\n"
    )
    assert result == expected


def test_render_line_diff_missing_newline_in_b_only():
    edits = [
        Edit("equal", "line1"),
        Edit("insert", "new"),
    ]
    result = render_line_diff(edits, a_ends_with_newline=True, b_ends_with_newline=False)
    expected = (
        "  line1\n"
        "+ new\n"
        r"\ No newline at end of file" + "\n"
    )
    assert result == expected


def test_render_line_diff_missing_newline_in_both():
    edits = [
        Edit("delete", "old"),
        Edit("insert", "new"),
    ]
    result = render_line_diff(edits, a_ends_with_newline=False, b_ends_with_newline=False)
    expected = (
        "- old\n"
        r"\ No newline at end of file" + "\n"
        "+ new\n"
        r"\ No newline at end of file" + "\n"
    )
    assert result == expected


def test_render_line_diff_changed_final_line_with_missing_newline_in_a():
    # Test case from approval: final line is replaced, A lacks newline, B has newline
    edits = [
        Edit("delete", "old"),
        Edit("insert", "new"),
    ]
    result = render_line_diff(edits, a_ends_with_newline=False, b_ends_with_newline=True)
    expected = (
        "- old\n"
        r"\ No newline at end of file" + "\n"
        "+ new\n"
    )
    assert result == expected


def test_render_line_diff_neither_missing_newline():
    edits = [
        Edit("equal", "a"),
        Edit("delete", "b"),
        Edit("insert", "c"),
    ]
    result = render_line_diff(edits, a_ends_with_newline=True, b_ends_with_newline=True)
    expected = (
        "  a\n"
        "- b\n"
        "+ c\n"
    )
    assert result == expected


def test_render_line_diff_only_equal_no_changes():
    # Both files end with newline, no deletes or inserts
    edits = [Edit("equal", "same")]
    result = render_line_diff(edits, True, True)
    assert result == "  same\n"


def test_render_line_diff_only_equal_missing_newline_in_both():
    # Both files identical but lack final newline
    # No delete or insert means no marker should appear (only equal lines present)
    edits = [Edit("equal", "same")]
    result = render_line_diff(edits, False, False)
    # With only equal edits, there's no last delete or insert, so no marker
    assert result == "  same\n"




# ============================================================================
# Fixture-based tests (spec §32)
# ============================================================================


from pathlib import Path
from diff_engine.line_diff import read_file, split_lines, diff_lines


@pytest.mark.parametrize(
    ("lang", "fixture"),
    [
        ("python", "constant"),
        ("python", "operator"),
        ("java", "constant"),
        ("cpp", "constant"),
    ],
)
def test_render_fixtures(lang, fixture):
    """Test golden outputs for Python/Java/C++ fixtures (spec §32)."""
    fixtures_dir = Path(__file__).parent / "fixtures" / lang
    ext = {"python": "py", "java": "java", "cpp": "cpp"}[lang]
    
    a_path = fixtures_dir / f"{fixture}_a.{ext}"
    b_path = fixtures_dir / f"{fixture}_b.{ext}"
    expected_path = fixtures_dir / f"{fixture}_expected.txt"
    
    a_text = read_file(str(a_path))
    b_text = read_file(str(b_path))
    
    a_lines, a_eol = split_lines(a_text)
    b_lines, b_eol = split_lines(b_text)
    
    edits = diff_lines(a_lines, b_lines)
    result = render_line_diff(edits, a_eol, b_eol)
    
    expected = read_file(str(expected_path))
    assert result == expected, f"Mismatch for {lang}/{fixture}"
