# Myers Diff Engine

A command-line Myers shortest-edit-script diff engine with line-level and character-level highlighting, implemented in Python.

## Features

- **Part A**: Line-level diff with `  ` (equal), `- ` (delete), `+ ` (insert) prefixes
- **Part B**: Character-level inline highlighting with `[-removed-]` and `{+added+}` markers
- **Genuine Myers algorithm**: Implements Myers' O(ND) shortest edit script with classic tie-breaking (deletes before inserts on same diagonal)
- **Real-world validated**: Tested against 36 genuine commit fixtures from 6 open-source repositories
- **Fast on typical diffs**: 3-5 million lines/sec on real-world source code with common subsequences

## Installation

Requires Python 3.11 or later.

```bash
# Clone the repository
git clone <repository-url>
cd myers-diff-engine

# No runtime dependencies needed
# Development: pytest 9.0.3 (optional, for running tests)
```

## Usage

### Command Line

```bash
# Part B (character-level highlighting, default)
python -m diff_engine file1.txt file2.txt

# Part A (line-level only)
python -m diff_engine --part A file1.txt file2.txt

# Part B (explicit)
python -m diff_engine --part B file1.txt file2.txt
```

### Exit Codes

- `0`: Files are identical (all lines equal)
- `1`: Files differ (at least one non-equal line)
- `2`: Error (file not found, encoding error, invalid arguments)

### Example Output

**Part A (line-level):**
```
  def process(data):
-     return data * 2
+     return data * 3
  
```

**Part B (character-level):**
```
  def process(data):
-     return data * [-2-]
+     return data * {+3+}
  
```

## Algorithm Overview

### Myers' Algorithm

The core implements Myers' O(ND) shortest edit script algorithm:

1. **Forward search**: Explores edit graph diagonals in rounds 0, 1, 2, ..., D until reaching the goal
2. **Backtracking**: Reconstructs the minimal edit script from the search trace
3. **Tie-breaking**: When multiple paths reach the same diagonal, prefer horizontal moves (deletes) over vertical moves (inserts)

**Time complexity**: O((N+M)·D) where N, M are input lengths and D is the edit distance  
**Space complexity**: O(D²) for storing the forward trace snapshots

See `PERFORMANCE.md` for detailed measurements.

### Character-Level Highlighting

For changed line pairs (Part B):

1. **Pairing**: Match i-th deleted line with i-th inserted line within each change block (positional, no similarity scoring)
2. **Character diff**: Run Myers on character sequences within paired lines
3. **Range merging**: Consecutive non-equal characters form `[-...-]` or `{+...+}` regions

### Line Splitting

- Splits on `\n` only (LF)
- Preserves `\r` within lines (observable CRLF vs LF difference)
- Tracks final newline presence separately
- UTF-8 strict decoding (errors fail with exit code 2)

## Project Structure

```
diff-engine/
├── src/diff_engine/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point
│   ├── cli.py               # Command-line interface
│   ├── models.py            # Edit[T] dataclass
│   ├── myers.py             # Core Myers algorithm
│   ├── line_diff.py         # File reading, line splitting, diffing
│   ├── char_diff.py         # Character-level ranges
│   ├── pairing.py           # Line pairing for Part B
│   └── renderer.py          # Part A and Part B output rendering
├── tests/
│   ├── test_*.py            # 239 tests total
│   ├── fixtures/            # Real-world corpus (36 genuine commits)
│   └── oracles.py           # Independent LCS oracle + replay verification
├── docs/
│   └── IMPLEMENTATION_PLAN.md  # Complete design decisions (D1-D5)
├── PERFORMANCE.md           # Performance measurements and analysis
├── benchmark.py             # Performance measurement script
├── pyproject.toml           # Project metadata and dependencies
└── README.md                # This file
```

## Testing

### Run All Tests

```bash
pytest
# 239 tests: 202 core + 37 corpus
```

### Test Categories

- **Myers core** (132 tests): Algorithm correctness, tie-breaking, adversarial cases
- **Line diff** (42 tests): File reading, line splitting, grouping, fixtures
- **Character diff** (21 tests): Pairing, character ranges, rendering
- **CLI** (7 tests): Argument parsing, exit codes, integration
- **Corpus** (37 tests): Real-world commits from git/git, pallets/flask, microsoft/TypeScript, openjdk/jdk, nodejs/node, nlohmann/json

### Test Oracles

- **Independent LCS**: Dynamic programming longest common subsequence for minimum edit distance verification
- **Replay**: Reconstructs original inputs from edit script to verify correctness
- **Golden scripts**: Hand-crafted minimal edit scripts for tie-breaking validation

## Design Decisions

All design decisions are documented and confirmed in `docs/IMPLEMENTATION_PLAN.md`:

- **D1 (Tie-breaking)**: Classic Myers rule; deletions before insertions
- **D2 (Newlines/encoding)**: UTF-8 strict, split on `\n` only, `\r` kept, LF vs CRLF observable
- **D3 (Pairing)**: i-th delete ↔ i-th insert within change blocks (positional, no similarity scoring)
- **D4 (Output)**: `  ` / `- ` / `+ ` prefixes; `[-x-]` / `{+x+}` character markers
- **D5 (CLI)**: `python -m diff_engine [--part {A,B}] FILE_A FILE_B`, default B, exit 0/1/2

## Performance

**Excellent on real-world diffs:**
- 10,000-line common prefix: 5.93 ms (3.4M lines/sec)
- 10,000-line common suffix: 5.06 ms (4.0M lines/sec)
- Real corpus files: 1-2 ms (5M+ lines/sec)

**Pathological worst case:**
- 2,000 fully different lines: 6.3 seconds (D=4,000, O(D²) behavior)

See `PERFORMANCE.md` for complete analysis and rationale for not optimizing.

## Known Limitations

1. **O(D²) worst case**: Fully different inputs with large D become slow (expected for standard Myers)
2. **No common prefix/suffix optimization**: Not implemented because it doesn't help the pathological case
3. **No line similarity scoring**: Character-level pairing is purely positional
4. **UTF-8 only**: No automatic encoding detection
5. **Memory usage**: Stores full forward trace (O(D²) snapshots)

## License

[Include your license here]

## References

- Myers, Eugene W. "An O(ND) Difference Algorithm and Its Variations." *Algorithmica* 1.1-4 (1986): 251-266.
- Implementation follows CLAUDE.md and myers_diff_project_full_spec.md specifications
