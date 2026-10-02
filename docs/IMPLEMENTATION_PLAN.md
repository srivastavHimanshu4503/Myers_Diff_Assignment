# Implementation Plan — Myers-Based Diff Engine

Sources: `CLAUDE.md` (rules, binding) and `myers_diff_project_full_spec.md`
(behaviour; provisional contracts in §44). Where they conflict, CLAUDE.md wins.

## 0. Ground rules applied to every phase

- One milestone at a time (M1 → M2 → M3 → M4); one PR per milestone (all its phases go on the same branch).
- Branch: `m<milestone>/p<milestone>-<first-issue#>-<slug>` from latest `origin/main` when starting the milestone.
  Example: M1 (P1.1–P1.5) uses `m1/p1-1-myers-core` for issues #1, #3, #7, etc.
- Gate: a phase starts only after its design is approved **and** the previous phase's commits are pushed. The milestone PR stays open until its final phase is done.
- Before each phase: mini-spec (Goal / Input / Output / Behaviour / Invariants / Acceptance / Tests) posted on the issue.
- After each phase: run tests, report the CLAUDE.md §20 Change Manifest, push the commits, stop and wait for developer approval. Never merge the PR.
- Conventional Commits, ≤72-char subject, `Refs #<issue>` footer on every commit, `Closes #<issue>` on the last commit of each phase.
- Standard library only at runtime. Only dev dependency: `pytest==9.0.3` (already installed). Property tests use `random.Random(seed)`, not Hypothesis.
- No `difflib`, no external diff command in `src/`.

Environment checked: Python 3.13.1, pytest 9.0.3, gh 2.97.0, repo on `main` with a single initial commit, remote `origin` on GitHub, no open issues.

## 1. Decisions to confirm before P-1 starts

| # | Decision | Provisional default (spec §44) | Blocks | Status |
|---|----------|--------------------------------|--------|--------|
| D1 | Tie-breaking | Classic Myers rule; deletes before inserts | P-1 | CONFIRMED 2026-10-02 |
| D2 | Newlines / encoding | UTF-8 strict, split on `\n` only, `\r` kept, final-newline flag | P-2 | OPEN |
| D3 | Pairing | i-th delete ↔ i-th insert inside a change block | P-3 | OPEN |
| D4 | Output | `  ` / `- ` / `+ ` prefixes; `[-x-]` / `{+x+}` char markers | P-2, P-3 | OPEN |
| D5 | CLI | `python -m diff_engine [--part {A,B}] A B`; exit 0/1/2 | P-4 | OPEN |

D1 is confirmed, so P-1 is unblocked. D2–D5 must each be settled before
their phase starts. If the official I/O spec arrives, it replaces them.

## 2. Target layout (built gradually, never ahead of the phase that needs it)

```text
pyproject.toml            P1.1
.gitignore                P1.1
.gitattributes            P1.1
.github/workflows/ci.yml  P1.1   (pytest on push/PR; needed for "CI green")
src/diff_engine/
  __init__.py             P1.1
  models.py               P1.2
  myers.py                P1.3–P1.4
  line_diff.py            P2.1–P2.2
  renderer.py             P2.3, extended P3.3
  pairing.py              P3.1
  char_diff.py            P3.2
  cli.py, __main__.py     P4.1
tests/
  oracles.py              P1.2   (independent LCS oracle + script replay; test-only)
  test_models.py          P1.2
  test_myers.py           P1.3–P1.5
  test_line_diff.py       P2.x
  test_renderer.py        P2.3, P3.3
  test_pairing.py         P3.1
  test_char_diff.py       P3.2
  test_cli.py             P4.1
  test_corpus.py          P4.2
  fixtures/               P2.3 (hand-made), P4.2 (real commits)
README.md                 P4.4
```

---

## P-1 — Myers core (milestone 1)

### P1.1 Project scaffolding
- Goal: an installable empty package and a test runner so later phases are verifiable.
- Files: `pyproject.toml` (setuptools, src layout, `requires-python >=3.11`,
  pytest config `testpaths = ["tests"]`, `pythonpath = ["src"]`), `.gitignore`,
  `.gitattributes` (`tests/fixtures/** -text`: this machine's Git converts
  LF→CRLF on checkout, which would silently corrupt CRLF / no-final-newline
  fixtures),
  `src/diff_engine/__init__.py`, `.github/workflows/ci.yml`,
  `tests/test_package.py` (one import smoke test, so pytest does not exit 5
  for "no tests collected" and CI is green from the first PR).
- Acceptance: `python -m pytest` → 1 passed.
- Commit: `build: add pyproject, package skeleton and CI`.

### P1.2 Edit model and test oracles
- `models.py`: `Operation = Literal["equal","insert","delete"]`,
  frozen generic `Edit[T](operation, value)`. Nothing else.
- `tests/oracles.py` (test code, independent of Myers):
  - `lcs_edit_distance(a, b)` — O(NM) DP; `N + M − 2·LCS` = true minimum D.
  - `replay(edits) -> (a, b)` — rebuilds A from equal+delete and B from equal+insert.
  - Rationale: DP LCS is an independent, provably correct oracle and scales
    further than enumerating scripts; it satisfies spec §34 / CLAUDE §13.3.
- Tests: oracle sanity on hand-computed cases.
- Commits: `feat(models): add Edit representation`, `test: add LCS oracle and replay helper`.

### P1.3 Forward search
- `myers.py`: private `_forward_trace(a, b) -> list[list[int]]` exploring D = 0,1,2,…;
  `V[k]` = furthest x on diagonal k (offset array, k ∈ [−D, D] step 2);
  snake extension `while x < N and y < M and a[x] == b[y]`; stops at (N, M);
  records a snapshot of V per D.
- Predecessor rule exactly as spec §44.1 (D1).
- Tests: `len(trace) − 1 == lcs_edit_distance(a, b)` for the §25–§30 cases and
  ~2 000 seeded random pairs (lengths 0–8, alphabet size 1–4).
- Commit: `feat(myers): implement forward shortest-path search`.

### P1.4 Backtracking and public API
- `myers_diff(a: Sequence[T], b: Sequence[T]) -> list[Edit[T]]`: walk the trace
  from (N, M) back to (0, 0), re-deriving each step's predecessor with the same
  rule, emitting snake → `equal`, right → `delete`, down → `insert`; reverse.
- Tests:
  - invariants for all cases + random pairs: `replay(edits) == (a, b)`,
    non-equal count == oracle D, identical inputs → equal-only;
  - golden determinism: `A = "ABCABBA"`, `B = "CBABAC"` →
    `-A -B =C +B =A =B -B =A +C` (to be hand-traced and confirmed at review);
  - works on `str` and `list[str]` alike (genericity);
  - same input twice → identical output.
- Commit: `feat(myers): reconstruct edit script by backtracking`,
  `test(myers): add invariant, golden and property tests`.

### P1.5 Adversarial review (spec §41 Agent 2)
- A separate reviewer hunts counterexamples (empty, repeats, alternating, ambiguous,
  10 000-line prefix/suffix, fully different). Reports first; no silent rewrites.
- Any failure → regression test that fails first, root-cause fix (CLAUDE §17).
- Commit (if needed): `test(myers): add adversarial regression cases`.

Milestone 1 done when: every §13.2 category is tested, oracle agreement holds on
all random pairs, golden script matches, developer can explain D, k, V[k], snake,
termination, backtracking and tie-breaking.

---

## P-2 — Line diff / Part A (milestone 2)

### P2.1 File reading and line splitting
- `line_diff.py`: `split_lines(text) -> tuple[list[str], bool]` (lines,
  ends_with_newline) per D2; `read_text(path) -> str` reading bytes and decoding
  UTF-8 strict; decode / OS errors raised as a clear `DiffInputError`
  (defined here, used by the CLI later).
- Tests: `""`, `"a"`, `"a\n"`, `"a\n\n"`, CRLF, mixed, `\x0c` not split,
  non-UTF-8 bytes → error, Unicode content.
- Commit: `feat(diff): add file reading and line splitting`.

### P2.2 Line diff and grouping
- `diff_lines(a_lines, b_lines)` = `myers_diff` on lines (no reimplementation).
- `group_edits(edits) -> list[Block]`: maximal runs of equal edits vs change
  blocks (`deleted: list[str]`, `inserted: list[str]`). Required by CLAUDE §24 P-2
  and consumed by the renderer and by pairing in P-3.
- Tests: §4 minimality example, §15 example, pure insert/delete, adjacent and
  separated changes, empty↔non-empty.
- Commit: `feat(diff): add line diff and change-block grouping`.

### P2.3 Part A renderer
- `renderer.py`: `render_line_diff(edits, a_eol, b_eol) -> str` per D4, including
  `\ No newline at end of file` placement.
- Fixtures: small Python/Java/C++ pairs from spec §32 (constant, operator,
  inserted/removed line, indentation, call change) with expected output files.
- Commit: `feat(render): add Part A line diff renderer`,
  `test(diff): add Python/Java/C++ fixtures`.

---

## P-3 — Character diff / Part B (milestone 3)

### P3.1 Changed-line pairing
- `pairing.py`: `pair_block(block) -> (pairs, unpaired_deleted, unpaired_inserted)`
  per D3. No similarity heuristics.
- Tests: 1↔1, 2↔2, 3↔1, 0↔2, 2↔0.
- Commit: `feat(pairing): pair deleted and inserted lines per block`.

### P3.2 Character ranges
- `char_diff.py`: `char_ranges(old, new) -> (deleted_ranges, inserted_ranges)`,
  calling `myers_diff(old, new)` on the strings directly and merging consecutive
  non-equal characters into half-open `(start, end)` ranges.
- Tests: `8000→8080`, same→same, `""→"abc"`, `"abc"→""`, `abc→xyz`, multiple
  separated changes, 2 000-char line, Unicode (`é`, `日本`, emoji). Invariant:
  removing deleted ranges from old and inserted ranges from new yields the same
  common string.
- Commit: `feat(chardiff): compute changed character ranges`.

### P3.3 Part B renderer
- Extend `renderer.py` with `render_char_diff(...)`: paired lines get inline
  markers; unpaired lines render as in Part A. Reuses Part A line formatting
  (no duplicated prefix logic).
- Tests: golden outputs for §17 and §32 fixtures.
- Commit: `feat(render): add Part B character highlighting`.

---

## P-4 — CLI and final hardening (milestone 4)

### P4.1 CLI
- `cli.py` (`argparse`), `__main__.py`; arguments and exit codes per D5;
  `DiffInputError` → message on stderr, exit 2.
- Tests (subprocess + `main(argv)`): both parts, identical files → exit 0,
  missing file, directory as input, bad `--part`, wrong arg count, undecodable file.
- Commit: `feat(cli): add command-line interface`.

### P4.2 Real-world corpus
- Collect ~20–30 before/after pairs from real open-source commits covering
  `.txt .py .c .cpp .java .ts` (small/large commits, repeated blocks, long lines,
  formatting-only changes, CRLF, no final newline).
- Independent check: for each pair store the expected minimal D obtained once
  with `git diff --no-index --minimal --numstat` (added + deleted) in a fixture
  manifest; tests assert our D equals it and `replay` holds. Git is used only
  to generate fixture data, never at runtime.
- Commit: `test(corpus): add real-commit fixtures and checks`.

### P4.3 Performance (measure first)
- Measure: 10 000-line common prefix/suffix, largest corpus file, a fully
  different 2 000-line pair (worst case for O(D²) trace memory).
- Optimise only if a measured case is unacceptable; candidate (in order):
  common prefix/suffix trimming (must re-verify golden tie-breaking), then the
  linear-space middle-snake variant. Otherwise record numbers and stop.
- Commit (only if needed): `perf(myers): ...`.

### P4.4 Documentation and final checklist
- `README.md`: purpose, run instructions, algorithm overview, I/O contract,
  structure, testing, known limitations.
- Walk spec §51 checklist and CLAUDE §21 final-release items; record evidence.
- Commit: `docs: add README and usage`.

---

## 3. Issue and branch list (one issue per phase, one PR per milestone)

Phases within the same milestone share one branch and PR. Each phase gets its own issue.

| Milestone | Phase | Issue | PR | Branch | Title |
|-----------|-------|-------|----|--------|-------|
| M1 | P1.1 | #1 | #2 (merged) | `m1/p1-1-scaffolding` | Project scaffolding and CI |
| M1 | P1.2 | #3 | #4 (merged) | `m1/p1-3-edit-model` | Edit model and test oracles |
| docs | - | #5 | #6 (merged) | `m1/p1-5-plan-branch-names` | Align plan branch names and issue table |
| M1 | P1.3 | #7 | #8 (merged) | `m1/p1-7-forward-search` | Myers forward search |
| docs | - | TBD | this PR | `m1/p1-docs-workflow` | Update workflow: one PR per milestone |
| M1 | P1.4 | TBD | TBD | `m1/p1-<issue#>-myers-core` | Myers backtracking and public API |
| M1 | P1.5 | TBD | same PR | same branch | Adversarial review of Myers core |
| M2 | P2.1 | TBD | TBD | `m2/p2-<issue#>-line-diff` | File reading and line splitting |
| M2 | P2.2 | TBD | same PR | same branch | Line diff and change-block grouping |
| M2 | P2.3 | TBD | same PR | same branch | Part A renderer and fixtures |
| M3 | P3.1 | TBD | TBD | `m3/p3-<issue#>-char-diff` | Changed-line pairing |
| M3 | P3.2 | TBD | same PR | same branch | Character-level ranges |
| M3 | P3.3 | TBD | same PR | same branch | Part B renderer |
| M4 | P4.1 | TBD | TBD | `m4/p4-<issue#>-cli` | CLI and exit codes |
| M4 | P4.2 | TBD | same PR | same branch | Real-world corpus tests |
| M4 | P4.3 | TBD | same PR | same branch | Performance measurement |
| M4 | P4.4 | TBD | same PR | same branch | README and final checklist |

**Note:** M1's first three phases (P1.1–P1.3) were completed under the old "one PR per phase" workflow and have already been merged. Starting with P1.4, the new workflow applies: all remaining M1 phases (P1.4–P1.5) will share one branch and PR.

## 4. Risk → mitigation (spec §50)

| Risk | Mitigation | Where |
|------|-----------|-------|
| Wrong backtracking | `replay` invariant on every test + random pairs | P1.4 |
| Non-minimal output | LCS oracle; git `--minimal` counts on corpus | P1.3, P4.2 |
| Tie-breaking drift | Fixed rule D1 + golden script | P1.4 |
| Repeated lines | Alphabet size 1–2 in random tests | P1.3–P1.5 |
| Pairing ambiguity | Explicit policy D3, isolated in `pairing.py` | P3.1 |
| Newline semantics | Policy D2, dedicated tests | P2.1 |
| Performance | Measure before optimising | P4.3 |
| Agent over-engineering | Phase gates, manifest, "which requirement needs this?" | all |
