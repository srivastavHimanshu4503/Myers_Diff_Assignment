"""Real-world corpus tests from diverse source patterns."""

import json
from pathlib import Path

import pytest

from diff_engine.line_diff import diff_lines, read_file, split_lines
from oracles import minimum_edit_distance, replay


def _discover_corpus_fixtures():
    """Discover all corpus fixture directories."""
    corpus_dir = Path(__file__).parent / "fixtures" / "corpus"
    if not corpus_dir.exists():
        return []
    
    fixtures = []
    for item in corpus_dir.iterdir():
        if item.is_dir() and (item / "metadata.json").exists():
            fixtures.append(item)
    return sorted(fixtures)


@pytest.mark.parametrize("fixture_dir", _discover_corpus_fixtures())
def test_corpus_fixture(fixture_dir):
    """Test a corpus fixture: minimal D and correct replay."""
    # Load metadata
    metadata_path = fixture_dir / "metadata.json"
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # Find before/after files
    before_files = list(fixture_dir.glob("before.*"))
    after_files = list(fixture_dir.glob("after.*"))
    
    assert len(before_files) == 1, f"Expected 1 before file in {fixture_dir}"
    assert len(after_files) == 1, f"Expected 1 after file in {fixture_dir}"
    
    before_path = before_files[0]
    after_path = after_files[0]
    
    # Read files
    before_text = read_file(str(before_path))
    after_text = read_file(str(after_path))
    
    before_lines, _ = split_lines(before_text)
    after_lines, _ = split_lines(after_text)
    
    # Compute diff
    edits = diff_lines(before_lines, after_lines)
    
    # Count non-equal edits (our D)
    actual_D = sum(1 for e in edits if e.operation != "equal")
    
    # Check minimality against metadata
    expected_D = metadata.get("expected_D")
    if expected_D is not None:
        assert actual_D == expected_D, (
            f"{fixture_dir.name}: expected D={expected_D}, got D={actual_D}"
        )
    
    # Check minimality against oracle
    oracle_D = minimum_edit_distance(before_lines, after_lines)
    assert actual_D == oracle_D, (
        f"{fixture_dir.name}: oracle D={oracle_D}, got D={actual_D}"
    )
    
    # Check replay correctness
    reconstructed_before, reconstructed_after = replay(edits)
    assert reconstructed_before == before_lines, f"{fixture_dir.name}: replay before mismatch"
    assert reconstructed_after == after_lines, f"{fixture_dir.name}: replay after mismatch"


def test_corpus_not_empty():
    """Ensure corpus fixtures exist."""
    fixtures = _discover_corpus_fixtures()
    assert len(fixtures) > 0, "No corpus fixtures found"
