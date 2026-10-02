# CLAUDE.md

## Project: Myers-Based Diff Engine

This repository implements a command-line diff engine in **Python** with
two layers:

1.  **Part A --- Line Diff:** Compute a minimal line-level edit script
    from file A to file B.
2.  **Part B --- Character Diff:** For changed lines, compute
    character-level differences and highlight the exact changed
    characters.

The core algorithm is **Myers' shortest edit script (SES) algorithm**.

The test corpus is expected to contain real text and source files,
including `.txt`, `.py`, `.c`, `.cpp`, `.java`, and `.ts`, many
originating from real open-source commits.

The supplied project notes are the algorithmic reference for the Myers
implementation. Do not replace the required algorithm with a generic
diff library.

------------------------------------------------------------------------

# 1. Mission and Engineering Principles

## 1.1 Primary goal

Build the **smallest correct implementation** that satisfies the project
specification.

Correctness comes before optimization, abstraction, and convenience.

The implementation must:

-   produce a minimal edit script;
-   be deterministic;
-   reconstruct the actual edit operations;
-   support line-level diffing;
-   support character-level highlighting;
-   work on realistic source files;
-   expose a clear command-line interface;
-   remain understandable to the developer.

## 1.2 Clarity over cleverness

-   Prefer obvious code over clever code.
-   Keep the Myers implementation close to the algorithm it represents.
-   Use descriptive names such as `edit_distance`, `diagonal`,
    `furthest_x`, and `edits`.
-   Avoid abstractions that hide the algorithm.
-   A new engineer should be able to trace a diff from input sequences
    to the resulting edit script.

## 1.3 Small, reversible steps

Work incrementally.

Each change should:

1.  have a clear purpose;
2.  be small enough to review;
3.  be independently testable;
4.  avoid unrelated refactoring.

Do not implement the entire application in one pass.

## 1.4 Production quality at every step

There are no throwaway implementations.

Do not create code with the intention of "cleaning it up later" if the
code can be written correctly within the current scope.

At the same time, do not implement functionality that belongs to a later
phase.

## 1.5 Developer understanding is mandatory

The developer must understand:

-   the edit graph;
-   `D`;
-   `k = x - y`;
-   the furthest-reaching `V[k]` state;
-   diagonal/snake extension;
-   termination;
-   backtracking;
-   tie-breaking;
-   edit-script representation;
-   changed-line pairing;
-   character-level diffing.

If an implementation cannot be explained, stop and explain it before
proceeding.

## 1.6 Fail fast and loudly

Invalid CLI usage, unreadable input files, invalid configuration, and
impossible internal states should fail at clear boundaries.

Do not:

-   silently ignore invalid input;
-   swallow exceptions;
-   return a plausible-looking but incorrect diff;
-   hide algorithmic failures behind generic fallbacks.

## 1.7 Debuggability is a feature

The pipeline should be inspectable:

``` text
Input files
    ↓
Line sequences
    ↓
Myers search
    ↓
Backtracking
    ↓
Edit script
    ↓
Changed-line grouping/pairing
    ↓
Character-level Myers
    ↓
Character ranges
    ↓
Renderer
    ↓
CLI output
```

When something fails, identify the first incorrect stage rather than
patching the final output.

------------------------------------------------------------------------

# 2. Scope Control --- Do Not Overengineer

This project is intentionally focused.

### Always follow these rules:

-   **Do not overengineer.**
-   **Always check for repetitive code before adding new code.**
-   **Only write code when there is an actual requirement for it.**
-   **Do not implement future functionality early.**
-   **Do not implement P-4 functionality in P-1.**
-   **Do not add infrastructure because it might be useful later.**
-   **Do not add abstractions because a larger production system might
    eventually need them.**
-   **Do not add a dependency when the standard library is sufficient.**
-   **Do not build a parser for Python, Java, C++, or TypeScript.**
-   **Do not introduce AST-based comparison unless the official
    specification explicitly requires it.**
-   **Do not replace Myers with `difflib`, a third-party diff library,
    or an external command.**
-   **Do not build a GUI or web interface unless explicitly required.**
-   **Do not add caching, databases, queues, services, or cloud
    infrastructure.**
-   **Do not create compatibility layers for hypothetical future
    requirements.**

The correct question before implementing something is:

> "Which current requirement requires this?"

If there is no answer, do not implement it.

------------------------------------------------------------------------

# 3. Development Workflow

## 3.1 One milestone at a time

Never implement multiple milestones simultaneously.

Do not write code for a future milestone while the current milestone is
unfinished.

Recommended progression:

``` text
P-1: Myers core
    ↓
P-2: Line diff
    ↓
P-3: Character diff/highlighting
    ↓
P-4: CLI/integration/final hardening
```

The exact milestone numbering must follow the repository's official task
specification if one is supplied.

The principle is permanent:

> **Do not implement P-4 in P-1.**

## 3.2 Phased rollout within a milestone

Large milestones should be split into small logical phases.

For every phase:

1.  explain the goal;
2.  explain the design;
3.  identify files that will change;
4.  implement only that phase;
5.  run the relevant tests;
6.  inspect the result;
7.  obtain developer confirmation;
8.  continue only after confirmation.

## 3.3 One issue per logical task

Each logical task should have one issue.

An issue should identify:

-   requirement;
-   phase;
-   scope;
-   acceptance criteria;
-   expected tests.

Do not combine unrelated changes into one issue or branch.

## 3.4 Spec before code

Any phase that introduces meaningful behavior should have a concise
specification before implementation.

The specification should state:

``` text
Goal
Input
Output
Behavior
Invariants
Acceptance criteria
Tests
```

Do not invent additional behavior that is not in the specification.

## 3.5 Explain before implementing

Before changing code, explain:

-   what is being built;
-   why it is needed;
-   where it belongs;
-   which existing code it interacts with;
-   which files will change;
-   how it will be tested.

Implementation follows design, not the other way around.

## 3.6 Approval gates

Do not automatically continue through all phases.

The expected loop is:

``` text
Design
  ↓
Developer approval
  ↓
Implementation
  ↓
Tests
  ↓
Developer verification
  ↓
Next phase
```

------------------------------------------------------------------------

# 4. Project Architecture Rules

## 4.1 Core architecture

The recommended architecture is:

``` text
                ┌─────────────────┐
                │   Myers Core    │
                │ Generic Seq A/B │
                └────────┬────────┘
                         │
                  Minimal edit script
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Line-level layer      Character-level layer
              │                     │
              ▼                     ▼
          Part A                 Part B
              │                     │
              └──────────┬──────────┘
                         ▼
                      Renderer
                         │
                         ▼
                        CLI
```

## 4.2 Myers must be generic

The Myers implementation should operate on sequences.

It should not know whether the elements are:

-   lines;
-   characters;
-   source-code tokens.

For example:

``` python
myers_diff(lines_a, lines_b)
```

and:

``` python
myers_diff(chars_a, chars_b)
```

should use the same algorithm.

## 4.3 Recommended responsibility boundaries

### `myers.py`

Responsible for:

-   shortest edit script search;
-   diagonal handling;
-   furthest-reaching state;
-   path reconstruction;
-   deterministic tie-breaking.

It must not contain:

-   file I/O;
-   terminal formatting;
-   language-specific logic;
-   CLI argument parsing.

### `models.py`

Responsible for the shared edit representation.

Example:

``` python
Edit(
    operation="equal",
    value="some line",
)
```

### `line_diff.py`

Responsible for:

``` text
file → lines → Myers → line edits
```

### `char_diff.py`

Responsible for:

``` text
changed line pair → characters → Myers → character edits
```

### `pairing.py`

Responsible for changed-line grouping/pairing if required by the
official output specification.

Do not prematurely add complex pairing logic before the required
behavior is known.

### `renderer.py`

Responsible only for converting internal results into the required
output format.

### `cli.py`

Responsible for:

-   parsing command-line arguments;
-   validating arguments;
-   reading files;
-   invoking the pipeline;
-   reporting boundary errors;
-   returning appropriate exit status.

------------------------------------------------------------------------

# 5. Code Generation Rules

## 5.1 Modify only what the current phase requires

Do not rewrite unrelated files.

Do not "clean up" unrelated code while implementing a feature.

If unrelated cleanup is genuinely necessary, create a separate task.

## 5.2 No placeholder or dead code

Do not add:

``` python
pass
```

or:

``` python
TODO: implement later
```

for functionality required by the current phase.

Intentional interface stubs are allowed only when they are explicitly
part of the current design.

## 5.3 Keep changes reviewable

Prefer:

``` text
small focused change
```

over:

``` text
large architectural rewrite
```

A reviewer should be able to answer:

> "What requirement does every changed line support?"

## 5.4 Avoid repetitive code

Before adding code:

1.  search the repository;
2.  check whether the behavior already exists;
3.  reuse the existing implementation where appropriate;
4.  extract shared logic only when duplication is real and the
    abstraction is simpler.

Do not create abstractions merely to avoid two similar lines of code.

## 5.5 Follow established structure

New files must be placed according to their responsibility.

Do not create:

``` text
utils/
helpers/
common/
misc/
```

as dumping grounds for unrelated functionality.

## 5.6 Comment the "why", not the "what"

Bad:

``` python
# Increment x by one
x += 1
```

Good:

``` python
# Extend the diagonal while elements match so the edit distance
# accounts only for insertions/deletions.
x += 1
```

The Myers implementation may contain comments explaining invariants and
non-obvious algorithmic decisions.

## 5.7 Consistency over personal preference

Match:

-   existing naming;
-   formatting;
-   project structure;
-   test conventions;
-   Python version;
-   dependency management.

Do not introduce a new style without a concrete reason.

------------------------------------------------------------------------

# 6. Myers Algorithm Rules

## 6.1 Required algorithm

The core line diff must use Myers' shortest edit script algorithm.

Do not substitute:

``` python
difflib
```

or another generic diff algorithm.

The algorithm is the core learning and implementation requirement.

## 6.2 Core concepts that must remain explicit

The implementation should preserve the concepts:

``` text
D = edit distance
k = x - y
V[k] = furthest reachable x
```

and:

``` text
diagonal/snake = matching elements
horizontal/vertical movement = insertion/deletion
```

## 6.3 Path reconstruction

Finding only the minimum `D` is insufficient.

The implementation must reconstruct the actual edit script.

Expected internal operations:

``` text
EQUAL
DELETE
INSERT
```

## 6.4 Minimality

For all tested inputs:

``` text
edit_script(A, B)
```

must use the minimum possible number of insertions and deletions.

For small inputs, validate this against an independent
brute-force/reference solver.

## 6.5 Determinism

If multiple shortest edit scripts exist, the implementation must follow
the deterministic behavior required by the project specification.

Do not introduce random choices.

Do not rely on unordered iteration where it can affect the result.

------------------------------------------------------------------------

# 7. Part A Rules --- Line Diff

Part A must:

1.  read two files;
2.  represent them as line sequences;
3.  invoke the Myers core;
4.  obtain a minimal edit script;
5.  render the required line-level output.

The core must remain independent of file I/O.

Example conceptual result:

``` text
EQUAL   "def add(a, b):"
DELETE  "    return a + b"
INSERT  "    return a + b + 1"
```

Do not implement character-level highlighting inside the Myers core.

------------------------------------------------------------------------

# 8. Part B Rules --- Character Diff

Part B must build on Part A.

Pipeline:

``` text
Line diff
   ↓
changed line groups
   ↓
changed deleted/inserted lines
   ↓
character sequences
   ↓
same Myers engine
   ↓
character edit ranges
   ↓
highlighted output
```

Do not implement a completely separate character-diff algorithm unless
the official specification requires behavior that cannot be expressed
through the existing Myers engine.

------------------------------------------------------------------------

# 9. Language Handling

The diff engine is language-agnostic.

Supported/tested extensions may include:

``` text
.txt
.py
.c
.cpp
.java
.ts
```

Do not create language-specific branches such as:

``` python
if extension == ".py":
    ...
elif extension == ".java":
    ...
```

unless the official requirements explicitly demand language-specific
behavior.

The engine compares text, not program semantics.

------------------------------------------------------------------------

# 10. Infrastructure Philosophy

## 10.1 No unnecessary infrastructure

This project does not inherently require:

-   databases;
-   Redis;
-   queues;
-   workers;
-   APIs;
-   cloud services;
-   containers;
-   message brokers;
-   external LLM services.

Do not add them.

## 10.2 Dependencies

Prefer the Python standard library.

Before adding a dependency, answer:

1.  What current requirement needs it?
2.  Can the standard library solve it?
3.  Does the dependency materially reduce complexity?
4.  Is its maintenance burden justified?

If not, do not add it.

## 10.3 Keep components replaceable without over-abstraction

A reusable Myers function is valuable.

A framework of interfaces around a single pure Python function is not.

Use abstraction only where it improves current clarity or testability.

------------------------------------------------------------------------

# 11. Git Workflow

Every task follows:

``` text
Issue
  ↓
Task branch
  ↓
Design
  ↓
Implementation
  ↓
Tests
  ↓
Logical commits
  ↓
Push with permission
  ↓
PR
  ↓
CI green
  ↓
Review
  ↓
Merge by authorised maintainer
```

## 11.1 Branches

Use short-lived branches.

Preferred pattern:

``` text
m<milestone>/p<phase>-<issue#>-<slug>
```

Example:

``` text
m1/p1-12-myers-core
```

Create the branch from the latest:

``` text
origin/main
```

## 11.2 Never push to main

Never push directly to:

``` text
origin/main
```

All changes reach main through a reviewed PR.

## 11.3 Push only with permission

Agents may:

-   create the task branch;
-   make local commits;
-   run tests;
-   prepare the PR.

Agents must not push or open/merge a PR unless the developer explicitly
authorizes that action for the task.

## 11.4 Never merge

Merging is performed by an authorised maintainer after:

-   CI passes;
-   required reviews pass;
-   repository rules are satisfied.

Preferred merge method:

``` text
rebase and merge
```

when supported by the repository workflow.

## 11.5 No history rewriting on shared branches

Do not:

``` bash
git push --force
git reset --hard
git rebase
```

on a pushed/shared branch without explicit developer approval.

------------------------------------------------------------------------

# 12. Commit Standards

## 12.1 One logical change per commit

Examples:

``` text
feat(myers): implement shortest edit path
test(myers): add repeated-sequence cases
feat(diff): add line-level renderer
feat(diff): add character-level highlighting
test(diff): add real-source fixtures
```

Do not mix:

``` text
feature + refactor + formatting + unrelated cleanup
```

in one commit.

## 12.2 Every commit should be healthy

Every commit should:

-   build/run;
-   pass relevant tests;
-   represent a coherent change.

This preserves useful `git bisect` behavior.

## 12.3 Commit subject

Use Conventional Commits:

``` text
feat
fix
refactor
test
docs
chore
perf
security
build
ci
```

Subject requirements:

-   imperative mood;
-   concise;
-   ≤ 72 characters;
-   no trailing period;
-   requirement/issue ID where applicable.

Example:

``` text
feat(myers): implement shortest edit script reconstruction
```

## 12.4 Commit body

For meaningful changes:

``` text
feat(myers): implement shortest edit script reconstruction

Reconstruct the minimal sequence of insertions, deletions and matches
from the furthest-reaching diagonal states so Part A can consume a
deterministic edit script.

Refs #12
```

Wrap the body at approximately 72 characters.

## 12.5 Footers

Use:

``` text
Refs #<issue>
```

on every commit.

Use:

``` text
Closes #<issue>
```

on the final commit of the PR when appropriate.

Use:

``` text
BREAKING CHANGE:
```

when applicable.

------------------------------------------------------------------------

# 13. Testing Expectations

## 13.1 Every phase must be verifiable

Every phase must end with:

1.  exact commands to run;
2.  expected result;
3.  explanation of what the test proves.

## 13.2 Test the algorithm, not only the output

At minimum test:

-   empty sequences;
-   identical sequences;
-   insertion;
-   deletion;
-   replacement;
-   repeated elements;
-   ambiguous matches;
-   multiple shortest scripts;
-   common prefixes;
-   common suffixes;
-   completely different sequences.

## 13.3 Minimality tests

For small sequences, use an independent brute-force/reference
implementation.

Verify:

``` text
Myers edit count == true minimum edit count
```

Do not use the same Myers implementation as both the implementation and
oracle.

## 13.4 Transformation invariant

Every edit script must satisfy:

``` text
apply(edits, A) == B
```

This should be automated.

## 13.5 Character-level tests

Test:

``` text
8000 → 8080
```

as well as:

``` text
same → same
"" → "abc"
"abc" → ""
"abc" → "xyz"
multiple separated changes
long lines
Unicode
```

## 13.6 Real-world tests

Use real source files and commit-derived fixtures where available.

Include:

``` text
.txt
.py
.c
.cpp
.java
.ts
```

Do not assume toy examples represent real-world behavior.

## 13.7 Failure paths

Test:

-   missing file;
-   unreadable file;
-   invalid CLI arguments;
-   invalid mode/option;
-   malformed input if the official format permits malformed input;
-   unexpected internal state.

Errors should be explicit and actionable.

------------------------------------------------------------------------

# 14. Property-Based Testing

Where practical, generate small random sequences.

For each pair:

``` python
A = random_sequence()
B = random_sequence()
edits = myers_diff(A, B)
```

Verify:

``` python
assert apply(edits, A) == B
```

Then verify minimality using a separate small-input oracle.

This is particularly effective at exposing:

-   diagonal mistakes;
-   backtracking bugs;
-   repeated-element bugs;
-   tie-breaking inconsistencies.

------------------------------------------------------------------------

# 15. Edge Cases

The implementation must explicitly consider:

``` text
empty file → empty file
empty file → non-empty file
non-empty file → empty file
identical files
completely different files
single-line files
single-character files
repeated lines
repeated characters
large common prefix
large common suffix
large changed block
multiple adjacent changes
multiple separated changes
long lines
Unicode
LF
CRLF
missing final newline
```

Exact newline behavior should follow the official project specification
when it is supplied.

------------------------------------------------------------------------

# 16. Performance Rules

Do not optimize before measuring.

The first objective is:

``` text
correct + minimal + deterministic
```

Only optimize after:

1.  correctness is established;
2.  realistic tests exist;
3.  a measurable performance problem is demonstrated.

Avoid:

-   speculative caching;
-   complex memory pools;
-   concurrency;
-   multiprocessing;
-   custom allocators;
-   premature micro-optimizations.

If performance becomes an issue, measure first and optimize the
identified bottleneck.

------------------------------------------------------------------------

# 17. Debugging Protocol

When something breaks, follow this exact order.

## Step 1 --- Reproduce

Use the smallest input that demonstrates the failure.

Record:

``` text
command
input files
expected output
actual output
```

## Step 2 --- Locate

Determine which stage failed:

``` text
file reading
↓
line parsing
↓
Myers forward search
↓
backtracking
↓
edit grouping
↓
character diff
↓
renderer
```

## Step 3 --- Read evidence

Inspect:

-   failing test;
-   intermediate edit script;
-   `D`;
-   `k`;
-   `V[k]`;
-   reconstructed path;
-   character operations.

Do not form a theory before examining evidence.

## Step 4 --- State a hypothesis

Write:

``` text
Hypothesis:
...

Evidence that supports it:
...

Observation that would disprove it:
...
```

## Step 5 --- Fix the root cause

Do not patch the rendered output to hide a wrong edit script.

Add a regression test that fails before the fix.

## Step 6 --- Verify

Run:

``` text
targeted test
+
full relevant test suite
```

Do not weaken the test to make the failure disappear.

------------------------------------------------------------------------

# 18. Forbidden Fixes

Never fix a failing test by:

-   disabling the test;
-   changing the expected output without understanding why;
-   using a non-minimal heuristic;
-   replacing Myers with another algorithm;
-   catching and ignoring the exception;
-   silently dropping a problematic input;
-   hardcoding a known fixture;
-   adding special cases for one test file;
-   widening behavior beyond the specification;
-   copying an external implementation without understanding it.

------------------------------------------------------------------------

# 19. AI Agent Operating Rules

AI coding agents must behave as engineering assistants, not autonomous
architects.

## Before coding

The agent must:

1.  inspect the repository;
2.  read relevant project documents;
3.  identify the active milestone/phase;
4.  inspect existing implementation;
5.  search for existing reusable code;
6.  state the proposed design;
7.  list expected file changes;
8.  identify tests.

## During coding

The agent must:

-   stay within the active phase;
-   make the smallest sufficient change;
-   avoid unrelated refactors;
-   reuse existing code;
-   keep the Myers algorithm understandable;
-   add tests with behavior changes;
-   avoid speculative infrastructure.

## After coding

The agent must report:

``` text
Summary
Changed files
Tests run
Test results
Known limitations
Next step
```

Do not automatically start the next phase.

------------------------------------------------------------------------

# 20. Required Change Manifest

Every completed change set must end with:

``` text
## Changed Files

### Added
- path/to/file.py

### Modified
- path/to/file.py

### Deleted
- none

## Commits
- <commit hash> <subject>

## Tests
- <command>
- <result>

## Verification
- <what was verified>

## Known Limitations
- <if any>
```

If a category has no changes, explicitly write:

``` text
- none
```

------------------------------------------------------------------------

# 21. Definition of Done

A phase is complete only when:

-   the current requirement is clearly identified;
-   architecture/design has been explained;
-   only the current phase was implemented;
-   no future-phase functionality was added;
-   no unrelated files were modified;
-   implementation is understandable;
-   relevant tests exist;
-   happy paths pass;
-   failure paths pass where applicable;
-   minimality is verified where applicable;
-   transformation correctness is verified;
-   deterministic behavior is verified;
-   real-world fixtures are tested where applicable;
-   documentation is updated when required;
-   Changed Files manifest is provided;
-   commit standards are followed;
-   developer has successfully verified the phase;
-   approval is received before the next phase begins.

For the final project release, additionally verify:

-   the official CLI contract;
-   all required supported extensions;
-   the complete real-world test corpus;
-   output format;
-   character highlighting;
-   performance expectations;
-   packaging/run instructions.

------------------------------------------------------------------------

# 22. Documentation Expectations

Keep documentation proportional to the project.

Required documentation should explain:

-   what the tool does;
-   how to run it;
-   algorithm overview;
-   input/output contract;
-   project structure;
-   testing;
-   known limitations.

Do not create a large documentation system unless the project actually
needs it.

A concise README plus focused design/spec documents is preferable to a
collection of redundant documents.

------------------------------------------------------------------------

# 23. Recommended Project Structure

A minimal structure is preferred:

``` text
.
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── src/
│   └── diff_engine/
│       ├── __init__.py
│       ├── myers.py
│       ├── models.py
│       ├── line_diff.py
│       ├── char_diff.py
│       ├── pairing.py
│       ├── renderer.py
│       └── cli.py
├── tests/
│   ├── test_myers.py
│   ├── test_line_diff.py
│   ├── test_char_diff.py
│   ├── test_cli.py
│   └── fixtures/
└── docs/
    └── specs/
```

This is a recommendation, not a mandate. If the existing repository
already has a different structure, follow the repository's established
structure instead of moving files unnecessarily.

------------------------------------------------------------------------

# 24. Current Project Roadmap

## P-1 --- Myers Core

### Goal

Implement and validate the generic Myers shortest edit script algorithm.

### Includes

-   sequence-to-sequence API;
-   `Edit` representation;
-   forward search;
-   diagonal processing;
-   furthest-reaching state;
-   path reconstruction;
-   deterministic behavior;
-   unit tests;
-   minimality verification.

### Does NOT include

-   CLI;
-   file handling;
-   character highlighting;
-   GitHub-style renderer;
-   language-specific behavior.

------------------------------------------------------------------------

## P-2 --- Line Diff

### Goal

Use the Myers engine to compare complete files line by line.

### Includes

-   file reading;
-   line sequence handling;
-   Part A edit output;
-   line-level grouping;
-   integration tests.

### Does NOT include

-   character highlighting;
-   future optimizations;
-   UI.

------------------------------------------------------------------------

## P-3 --- Character Diff

### Goal

Add character-level highlighting for changed lines.

### Includes

-   changed-line pairing;
-   character sequence generation;
-   reuse of Myers;
-   changed-character ranges;
-   Part B output;
-   character-level tests.

### Does NOT include

-   unrelated output formats;
-   UI;
-   semantic code analysis.

------------------------------------------------------------------------

## P-4 --- CLI and Final Hardening

### Goal

Finalize the command-line program according to the official project
specification.

### Includes

-   final CLI contract;
-   input validation;
-   required output format;
-   integration;
-   real-world corpus validation;
-   performance validation;
-   final documentation.

Do not implement P-4 features during P-1.

------------------------------------------------------------------------

# 25. Final Engineering Rule

The guiding rule for this project is:

> **Implement exactly what the current requirement needs, prove that it
> works, and only then move forward.**

When deciding whether to add code, ask:

``` text
Is this required now?
        │
        ├── No → Do not implement it.
        │
        └── Yes
             ↓
     Does it already exist?
             │
             ├── Yes → Reuse it.
             │
             └── No
                  ↓
        What is the smallest
        correct implementation?
```

The goal is not to build the largest diff engine possible.

The goal is to build a **correct, minimal, deterministic, understandable
Myers-based diff engine** with the exact capabilities required by the
assignment.
