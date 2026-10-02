import subprocess
import tempfile
from pathlib import Path

import pytest

from diff_engine.cli import main


def test_cli_identical_files_exit_0():
    """Identical files should exit with code 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.txt"
        b = Path(tmpdir) / "b.txt"
        a.write_bytes(b"hello\nworld\n")
        b.write_bytes(b"hello\nworld\n")

        result = main([str(a), str(b)])
        assert result == 0


def test_cli_different_files_exit_1():
    """Different files should exit with code 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.txt"
        b = Path(tmpdir) / "b.txt"
        a.write_bytes(b"hello\n")
        b.write_bytes(b"world\n")

        result = main([str(a), str(b)])
        assert result == 1


def test_cli_missing_file_exit_2(capsys):
    """Missing file should exit with code 2 and print error to stderr."""
    result = main(["nonexistent_a.txt", "nonexistent_b.txt"])
    assert result == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "nonexistent_a.txt" in captured.err


def test_cli_invalid_part_exit_2():
    """Invalid --part argument should exit with code 2."""
    result = main(["--part", "C", "a.txt", "b.txt"])
    assert result == 2


def test_cli_part_a():
    """Part A should render line diff only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.txt"
        b = Path(tmpdir) / "b.txt"
        a.write_bytes(b"old line\n")
        b.write_bytes(b"new line\n")

        # Capture output by redirecting stdout
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = main(["--part", "A", str(a), str(b)])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert result == 1
        assert "- old line" in output
        assert "+ new line" in output
        # Part A should not have character markers
        assert "[-" not in output
        assert "{+" not in output


def test_cli_part_b_default():
    """Part B (default) should render character diff."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.txt"
        b = Path(tmpdir) / "b.txt"
        a.write_bytes(b"value = 100\n")
        b.write_bytes(b"value = 200\n")

        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = main([str(a), str(b)])  # No --part, should default to B
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert result == 1
        # Part B should have character markers
        assert "[-" in output or "{+" in output


def test_cli_subprocess():
    """Test via subprocess to verify python -m diff_engine works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.txt"
        b = Path(tmpdir) / "b.txt"
        a.write_bytes(b"same\n")
        b.write_bytes(b"same\n")

        # Run with PYTHONPATH set to src directory
        import os
        env = os.environ.copy()
        src_path = Path(__file__).parent.parent / "src"
        env["PYTHONPATH"] = str(src_path)

        result = subprocess.run(
            ["python", "-m", "diff_engine", str(a), str(b)],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
