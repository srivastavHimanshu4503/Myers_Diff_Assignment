# Real-World Corpus Test Fixtures

This directory contains **29 genuine before/after file pairs** extracted from actual commits in public open-source repositories. These fixtures validate the Myers diff engine against real-world changes.

## Repositories and Coverage

| Language | Count | Source Repositories |
|----------|-------|---------------------|
| Text (.txt, .md) | 8 | git/git |
| Python (.py) | 8 | pallets/flask |
| TypeScript (.ts) | 5 | microsoft/TypeScript |
| Java (.java) | 4 | openjdk/jdk |
| JavaScript (.js) | 4 | nodejs/node |
| **Total** | **29** | **5 repositories** |

## Fixture Structure

Each fixture directory contains:

```
<id>/
├── before.<ext>       # File content at parent commit
├── after.<ext>        # File content at commit
└── metadata.json      # Full provenance and expected_D
```

### Metadata Format

```json
{
  "repo": "https://github.com/owner/repo",
  "commit": "<full-40-char-sha>",
  "parent": "<parent-commit-sha>",
  "path": "relative/path/to/file",
  "language": "python|java|typescript|javascript|text",
  "description": "First line of commit message",
  "expected_D": 42
}
```

- **repo**: GitHub repository URL
- **commit**: Full commit SHA where the change was made
- **parent**: Full parent commit SHA (the "before" state)
- **path**: File path within the repository
- **language**: Programming language or file type
- **description**: First 80 characters of the commit message
- **expected_D**: Minimal edit distance (calculated once during fixture creation using our diff engine)

## Validation

The corpus test (`tests/test_corpus.py`) verifies for each fixture:

1. **Minimality**: Our diff produces `D == expected_D`
2. **Oracle agreement**: `D == minimum_edit_distance(before, after)` (independent LCS-based calculation)
3. **Replay correctness**: `replay(our_edits) == (before_lines, after_lines)`

## Real-World Patterns Tested

These genuine commits cover:

- **Documentation updates**: typo fixes, formatting changes
- **Code refactoring**: variable extraction, conditional optimization  
- **Bug fixes**: parameter validation, error handling
- **Feature additions**: new methods, additional checks
- **Configuration changes**: option updates, deprecations
- **Mixed changes**: multi-line insertions/deletions

## Fixture Authenticity

Every fixture is traceable to its source commit:

```bash
# Verify fixture txt_001
git clone --depth 1 https://github.com/git/git.git temp
cd temp
git show 54c2884e8b:l10n/AGENTS.md > before.md  # parent
git show 54c2884e8b:l10n/AGENTS.md > after.md   # commit
```

All fixtures were extracted programmatically from cloned repositories using Git commands. No manual edits or synthetic modifications.

## Notes

- Byte-exact content: CRLF, final newlines, and encoding preserved as committed
- Protected by `.gitattributes`: `tests/fixtures/** -text` prevents Git newline conversion
- Clone depth: Fixtures extracted from `--depth 150` clones for faster processing
- Selection criteria: Small commits (1-3 files changed), understandable diffs, diverse patterns
- No merge commits, generated files, or binary diffs

## Fixture Collection

Fixtures were collected using `extract_corpus.py` (development tool, not shipped):

1. Clone repositories with `--depth 150 --single-branch`
2. Find commits modifying 1-3 files matching target extensions
3. Extract before (parent) and after (commit) content via `git show`
4. Calculate expected_D using our diff engine
5. Store with full provenance metadata

Total collection time: ~5 minutes for all 5 repositories.
