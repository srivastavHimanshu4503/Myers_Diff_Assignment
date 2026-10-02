# Test Corpus

This directory contains 20 diverse real-world-style fixtures testing the Myers diff engine.

## Coverage by Language

- **C** (4 fixtures): c_001, c_002, c_003, c_004
  - Const parameter addition
  - Constant deletion
  - Type change (int → unsigned)
  - Long line modification

- **C++** (3 fixtures): cpp_001, cpp_002, cpp_003
  - Method addition
  - Field addition (capacity)
  - Namespace wrapping

- **Java** (3 fixtures): java_001, java_002, java_003
  - Method rename
  - Multiline addition (enabled flag + logging)
  - Modifier changes (final class/field, version bump)

- **Python** (4 fixtures): py_001, py_002, py_003, py_004
  - Constant change
  - Comment insertion
  - Import reordering
  - Error handling change (exception → default value)

- **TypeScript** (3 fixtures): ts_001, ts_002, ts_003
  - Optional property marker
  - Variable extraction refactoring
  - Config value updates

- **Text** (3 fixtures): txt_001, txt_002, txt_003
  - No final newline handling
  - Repeated line patterns
  - CRLF line endings (Windows style)

## Diff Patterns Tested

- **Simple replacements**: constant changes, type changes
- **Insertions**: comments, methods, fields
- **Deletions**: unused constants
- **Reordering**: import statements (detected as delete+insert)
- **Multiline changes**: class modifications, wrapping
- **Edge cases**: no final newline, CRLF, long lines, repeated content

## Metadata Format

Each fixture directory contains:
- `before.<ext>`: original file content
- `after.<ext>`: modified file content
- `metadata.json`: test metadata including:
  - `source`: origin description
  - `language`: programming language
  - `description`: what changed
  - `expected_D`: minimal edit distance (calculated once, stored for test determinism)

## Validation

The corpus test (`test_corpus.py`) verifies for each fixture:
1. **Minimality**: `actual_D == expected_D` (from metadata)
2. **Oracle agreement**: `actual_D == minimum_edit_distance(before, after)`
3. **Replay correctness**: `replay(edits) == (before_lines, after_lines)`

All fixtures use exact byte content with no newline conversion (protected by `.gitattributes`).
