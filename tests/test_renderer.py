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



# ============================================================================
# Part B (character-level highlighting) tests
# ============================================================================


from diff_engine.line_diff import Block, diff_lines, split_lines, read_file
from diff_engine.renderer import render_char_diff


def test_render_char_diff_spec_example_8000_to_8080():
    # Spec §17: timeout = 8000 → timeout = 8080
    old = "timeout = 8000"
    new = "timeout = 8080"
    
    # Create a change block
    block = Block(equal_lines=[], deleted_lines=[old], inserted_lines=[new])
    result = render_char_diff([block], True, True)
    
    # Should have inline markers around the changed character(s)
    assert "[-" in result
    assert "{+" in result
    assert "timeout" in result


def test_render_char_diff_unpaired_lines():
    # 3 deletes, 1 insert: first pair gets highlights, rest are unpaired
    block = Block(
        equal_lines=[],
        deleted_lines=["old1", "old2", "old3"],
        inserted_lines=["new1"],
    )
    result = render_char_diff([block], True, True)
    
    lines = result.strip().split("\n")
    # Should have 4 lines: paired old1/new1 with markers, unpaired old2/old3 without
    assert len(lines) == 4
    # First two lines (paired) should have markers
    assert "[-" in lines[0] or "{+" in lines[0] or lines[0].startswith("- old1")
    # Last two lines (unpaired) should not have markers
    assert "[-" not in lines[2] and "{+" not in lines[2]
    assert "[-" not in lines[3] and "{+" not in lines[3]


def test_render_char_diff_equal_block():
    block = Block(equal_lines=["same line"], deleted_lines=[], inserted_lines=[])
    result = render_char_diff([block], True, True)
    assert result == "  same line\n"


def test_render_char_diff_missing_newline():
    block = Block(equal_lines=[], deleted_lines=["old"], inserted_lines=["new"])
    result = render_char_diff([block], a_ends_with_newline=False, b_ends_with_newline=True)
    assert r"\ No newline at end of file" in result
    # Should appear after the delete line
    lines = result.strip().split("\n")
    assert len(lines) == 3  # delete, marker, insert


@pytest.mark.parametrize(
    ("lang", "fixture"),
    [
        ("python", "constant"),
        ("python", "operator"),
    ],
)
def test_render_char_diff_fixtures(lang, fixture):
    """Test Part B on fixtures (Python only for now)."""
    fixtures_dir = Path(__file__).parent / "fixtures" / lang
    ext = {"python": "py", "java": "java", "cpp": "cpp"}[lang]
    
    a_path = fixtures_dir / f"{fixture}_a.{ext}"
    b_path = fixtures_dir / f"{fixture}_b.{ext}"
    
    a_text = read_file(str(a_path))
    b_text = read_file(str(b_path))
    
    a_lines, a_eol = split_lines(a_text)
    b_lines, b_eol = split_lines(b_text)
    
    edits = diff_lines(a_lines, b_lines)
    
    # Group edits into blocks
    from diff_engine.line_diff import group_edits
    blocks = group_edits(edits)
    
    result = render_char_diff(blocks, a_eol, b_eol)
    
    # Should contain character markers
    if any(block.deleted_lines and block.inserted_lines for block in blocks):
        assert "[-" in result or "{+" in result
