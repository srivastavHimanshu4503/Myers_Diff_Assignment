# Myers-Based Diff Engine --- Project Specification & Implementation Guide

> **Project:** Build a command-line diff engine that reproduces the core
> behavior of a modern source-code diff: minimal line-level edits plus
> character-level highlighting inside changed lines.
>
> **Primary language:** Python
>
> **Supported source languages:** Python, Java, C++
>
> **Expected input corpus:** Real text/source files, including `.txt`,
> `.py`, `.c`, `.cpp`, `.java`, and `.ts`, with many files originating
> from real open-source commits.
>
> **Core algorithm:** Myers shortest edit script algorithm.

------------------------------------------------------------------------

## 1. Executive Summary

The project is a command-line implementation of a two-stage diff engine.

Whenever a version-control system displays a change between two files,
there are two distinct problems:

1.  **Line-level change detection**
    -   Determine which lines are unchanged.
    -   Determine which lines were deleted.
    -   Determine which lines were inserted.
    -   The resulting edit script must be **minimal**, meaning it uses
        the fewest possible insertions and deletions.
2.  **Character-level change highlighting**
    -   For a pair of changed lines, determine the exact characters that
        differ.
    -   Highlight those character ranges inside the deleted and inserted
        lines.
    -   Example: changing `8000` to `8080` should identify the changed
        digits rather than treating the entire line as uniformly
        changed.

The project therefore consists of a reusable Myers diff engine followed
by two consumers:

``` text
                    ┌───────────────────────┐
                    │       File A          │
                    └───────────┬───────────┘
                                │
                                │
                    ┌───────────▼───────────┐
                    │    Myers Diff Engine   │
                    │   Shortest Edit Path  │
                    └───────────┬───────────┘
                                │
                    Minimal line edit script
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
      ┌───────────────┐                  ┌──────────────────┐
      │    Part A     │                  │      Part B      │
      │  Line Diff    │                  │ Character Diff   │
      └───────────────┘                  └────────┬─────────┘
                                                  │
                                           Myers again, but
                                           on characters
                                                  │
                                                  ▼
                                      Character-level ranges
                                      / GitHub-style highlights
```

The supplied Myers notes explain the shortest-edit-script framing, edit
graph, diagonals, and the idea of extending along matching diagonals.
The notes also discuss reconstruction of an edit script, equal-length
shortest alternatives, the relationship to Git, and the three-way merge
context. These concepts form the algorithmic foundation of this project.

------------------------------------------------------------------------

# 2. Problem Statement

Given two files:

``` text
A = original file
B = modified file
```

produce a minimal transformation from `A` into `B`.

At line level, the transformation is expressed using:

-   `EQUAL`
-   `DELETE`
-   `INSERT`

For example:

``` text
A:

def add(a, b):
    return a + b
```

``` text
B:

def add(a, b):
    return a + b + 1
```

A conceptual line diff is:

``` diff
  def add(a, b):
-     return a + b
+     return a + b + 1
```

Part B then compares the changed lines at character granularity.

For example:

``` text
old: return value = 8000
new: return value = 8080
```

The line-level algorithm tells us that these two lines are different.
The character-level algorithm should then identify the precise changed
character positions.

------------------------------------------------------------------------

# 3. Project Goals

## 3.1 Primary goals

The implementation must:

1.  Compare two files.
2.  Produce a minimal line-level diff.
3.  Represent the result as a deterministic edit script.
4.  Identify deleted lines.
5.  Identify inserted lines.
6.  Preserve unchanged lines.
7.  Perform character-level comparison for changed lines.
8.  Identify exact changed character ranges.
9.  Present those ranges as highlights.
10. Work on normal text and source-code files.
11. Operate through a command-line interface.
12. Handle realistic source files rather than only toy examples.

## 3.2 Non-goals

The core algorithm should **not** depend on:

-   Python syntax.
-   Java syntax.
-   C++ syntax.
-   TypeScript syntax.
-   AST parsing.
-   semantic understanding of the program.
-   variable names.
-   function names.
-   comments versus code.

At the diff-engine level, a source file is simply an ordered sequence of
lines, and a line is an ordered sequence of characters.

------------------------------------------------------------------------

# 4. Why Minimality Matters

A valid diff is not necessarily a good diff.

Suppose:

``` text
A:
a
b
c
d
```

and:

``` text
B:
a
b
X
c
d
```

A non-minimal algorithm could report:

``` diff
- a
- b
- c
- d
+ a
+ b
+ X
+ c
+ d
```

That transforms A into B, but it is clearly not the shortest edit
script.

A minimal algorithm instead reports:

``` diff
  a
  b
+ X
  c
  d
```

The project requirement therefore means:

> Find the smallest possible number of insertions and deletions needed
> to transform the sequence of lines in A into the sequence of lines in
> B.

This is the central reason Myers' algorithm is being used.

------------------------------------------------------------------------

# 5. Myers Algorithm: Conceptual Foundation

The supplied notes describe the problem as finding a shortest edit
script between two sequences.

For two sequences `A` and `B`, imagine an edit graph.

Let:

``` text
x = position in A
y = position in B
```

A point:

``` text
(x, y)
```

represents a state in the comparison.

Three types of movement are relevant:

``` text
Horizontal movement (x + 1)        → deletion  of A[x]
Vertical movement   (y + 1)        → insertion of B[y]
Diagonal movement   (x + 1, y + 1) → match, only when A[x] == B[y]
```

Because `x` indexes A, moving right consumes an element of A without
producing anything in B, which is a deletion. Moving down produces an
element of B, which is an insertion. (Earlier drafts of this document
had these two reversed.)

A diagonal move is free because it represents an element that already
matches.

An insertion or deletion increases the edit distance.

Therefore, a complete transformation corresponds to a path through the
graph from:

``` text
(0, 0)
```

to:

``` text
(N, M)
```

where:

``` text
N = length of A
M = length of B
```

The goal is to find the path with the smallest number of non-diagonal
moves.

The supplied notes visualize this edit graph and describe diagonal
movement as the matching portion of the edit path.

------------------------------------------------------------------------

# 6. Edit Distance `D`

Let:

``` text
D = number of insertions + number of deletions
```

The algorithm explores paths in increasing order of `D`:

``` text
D = 0
D = 1
D = 2
D = 3
...
```

The first time the algorithm reaches the endpoint:

``` text
(N, M)
```

it has found a shortest edit script.

This is the central shortest-path idea behind Myers' algorithm.

------------------------------------------------------------------------

# 7. Diagonals and `k`

A key Myers concept is:

``` text
k = x - y
```

Every point with the same value of:

``` text
x - y
```

lies on the same diagonal.

For example:

``` text
(0, 0)
(1, 1)
(2, 2)
(3, 3)
```

all belong to:

``` text
k = 0
```

The algorithm does not need to store every point of every possible path.

Instead, it tracks how far the best known path reaches on each diagonal.

This is the key optimization that makes Myers substantially more
efficient than naively enumerating every possible edit path.

------------------------------------------------------------------------

# 8. Furthest-Reaching Point

For each diagonal `k`, Myers tracks the furthest `x` coordinate reached
by a path with a particular edit distance `D`.

Conceptually:

``` text
V[k] = furthest x reached on diagonal k
```

Once `x` is known:

``` text
y = x - k
```

can be recovered.

The algorithm then tries to extend the path along the diagonal for as
long as elements continue matching.

Conceptually:

``` text
while A[x] == B[y]:
    x += 1
    y += 1
```

This is often called following or extending a **snake** along the
diagonal.

The supplied notes emphasize that diagonal movement is free and that
Myers tracks the furthest-reaching point on each diagonal.

------------------------------------------------------------------------

# 9. High-Level Myers Procedure

A simplified conceptual form is:

``` text
D = 0

while True:

    for each reachable diagonal k at edit distance D:

        choose the best predecessor

        move by one insertion or deletion

        follow matching elements diagonally

        record furthest-reaching x

        if (x, y) == (N, M):
            shortest path found
```

The exact implementation should be based on the algorithm studied in the
project notes rather than treating this pseudocode as a complete
implementation.

The most important invariant is:

> At edit distance `D`, maintain the furthest-reaching position on each
> reachable diagonal.

------------------------------------------------------------------------

# 10. Why the Algorithm Is Minimal

The algorithm explores paths in increasing order of edit distance:

``` text
0 → 1 → 2 → 3 → ...
```

Therefore, when the endpoint is reached for the first time at some `D`,
there cannot be a solution requiring fewer edits.

This is what gives the algorithm its shortest-edit-script property.

The project must preserve this property rather than using a heuristic
that merely produces visually reasonable diffs.

------------------------------------------------------------------------

# 11. Multiple Shortest Edit Scripts

An important edge case is that multiple shortest edit scripts can have
the same length.

For example, two different sequences of insertions/deletions may both
transform A into B using the same minimum number of operations.

The supplied notes explicitly discuss this situation and Myers'
preference when multiple shortest alternatives exist.

This matters because the implementation must be **deterministic**.

It is not sufficient for the program to return any valid minimum-length
answer if the expected output format requires a specific
traversal/tie-breaking behavior.

Therefore:

``` text
Minimality
+
Deterministic tie-breaking
=
Stable diff output
```

This should be covered by tests.

------------------------------------------------------------------------

# 12. From Shortest Path to Edit Script

Finding the shortest distance alone is insufficient.

The program ultimately needs the actual operations:

``` text
EQUAL
DELETE
INSERT
```

Therefore, the implementation needs path reconstruction/backtracking.

A conceptual result is:

``` python
[
    ("equal", "line 1"),
    ("equal", "line 2"),
    ("delete", "old line"),
    ("insert", "new line"),
    ("equal", "line 5"),
]
```

This intermediate representation should be separated from output
formatting.

------------------------------------------------------------------------

# 13. Recommended Internal Representation

Use a small, explicit representation for edit operations.

For example:

``` python
from dataclasses import dataclass
from typing import Literal

Operation = Literal["equal", "insert", "delete"]

@dataclass
class Edit:
    operation: Operation
    value: str
```

A diff can then be represented as:

``` python
[
    Edit("equal", "def add(a, b):"),
    Edit("delete", "    return a + b"),
    Edit("insert", "    return a + b + 1"),
]
```

This separation is important because the same edit script can be
consumed by:

-   a plain diff formatter,
-   a character-diff layer,
-   tests,
-   a future JSON output mode,
-   a future HTML renderer.

------------------------------------------------------------------------

# 14. Part A --- Line-Level Diff

Part A operates on lines.

The pipeline is:

``` text
File A
  ↓
Read text
  ↓
Split into lines
  ↓
Sequence A

File B
  ↓
Read text
  ↓
Split into lines
  ↓
Sequence B

Sequence A + Sequence B
  ↓
Myers
  ↓
Minimal edit script
  ↓
Line diff output
```

The core algorithm should receive sequences rather than filenames.

For example:

``` python
diff(
    ["a", "b", "c"],
    ["a", "x", "c"]
)
```

This allows the algorithm to be reused for character-level diffing.

------------------------------------------------------------------------

# 15. Part A Example

Input A:

``` text
def square(x):
    return x * x
```

Input B:

``` text
def square(x):
    return x ** 2
```

The line-level result is conceptually:

``` diff
  def square(x):
-     return x * x
+     return x ** 2
```

The exact presentation format depends on the project's later-provided
I/O specification.

The important internal result is:

``` text
EQUAL   "def square(x):"
DELETE  "    return x * x"
INSERT  "    return x ** 2"
```

------------------------------------------------------------------------

# 16. Part B --- Character-Level Diff

Part B builds on Part A.

It should not independently rediscover which lines changed.

Instead:

``` text
Part A
  ↓
identify changed line regions
  ↓
pair corresponding deleted/inserted lines
  ↓
run Myers again on characters
  ↓
character-level operations
  ↓
highlight changed characters
```

This is an important architectural principle:

> Use one generic Myers engine at different granularities.

The same algorithm can compare:

``` text
lines
```

or:

``` text
characters
```

because both are simply sequences.

------------------------------------------------------------------------

# 17. Character Diff Example

Suppose:

``` text
old = "timeout = 8000"
new = "timeout = 8080"
```

At line level:

``` diff
- timeout = 8000
+ timeout = 8080
```

At character level, most of the sequence matches:

``` text
timeout = 8 0 0 0
timeout = 8 0 8 0
             ↑
```

The character-level algorithm should isolate the differing region rather
than highlighting the complete line.

The renderer can then represent the changed range using the project's
required output convention.

------------------------------------------------------------------------

# 18. Why Character Diff Should Reuse Myers

It is tempting to write a separate character comparison algorithm.

That is unnecessary.

The core operation is identical:

``` text
Sequence A → Sequence B
```

For Part A:

``` text
Sequence = lines
```

For Part B:

``` text
Sequence = characters
```

Therefore:

``` python
myers_diff(lines_a, lines_b)

myers_diff(chars_a, chars_b)
```

can share the same algorithmic implementation.

This reduces duplicated logic and makes correctness easier to reason
about.

------------------------------------------------------------------------

# 19. Changed-Line Pairing

There is one important design problem between Part A and Part B.

A line-level diff can contain groups such as:

``` text
DELETE
DELETE
INSERT
INSERT
```

or:

``` text
DELETE
INSERT
```

Part B needs to determine which deleted line(s) should be compared with
which inserted line(s) for character highlighting.

This behavior should be made explicit rather than hidden inside the
Myers core.

Recommended separation:

``` text
Myers core
    ↓
raw edit script
    ↓
line-diff grouping
    ↓
changed-line pairing
    ↓
character diff
```

The exact pairing policy should follow the final project specification
once the weekend tooling/output requirements are provided.

Do not hard-code assumptions about pairing until the expected output
format is known.

------------------------------------------------------------------------

# 20. Supported Languages

The project states that the supported languages are:

-   Python
-   Java
-   C++

The broader test corpus may contain:

-   `.txt`
-   `.py`
-   `.c`
-   `.cpp`
-   `.java`
-   `.ts`

This suggests that the diff engine should remain **language-agnostic**.

For example:

``` text
foo.py
foo.cpp
foo.java
foo.ts
```

should all pass through the same line-based engine.

No language parser should be required for the basic diff.

------------------------------------------------------------------------

# 21. Suggested Architecture

A clean implementation can use:

``` text
myers-diff/
│
├── src/
│   └── diff_engine/          importable package (CLAUDE.md §23),
│       │                     enables `python -m diff_engine`
│       ├── __init__.py
│       ├── __main__.py       delegates to cli.main
│       ├── myers.py          generic Myers algorithm
│       ├── models.py         Edit representation
│       ├── line_diff.py      file/line processing
│       ├── char_diff.py      character-level processing
│       ├── pairing.py        changed-line pairing
│       ├── renderer.py       output formatting
│       └── cli.py            command-line interface
│
├── tests/
│   ├── test_myers.py
│   ├── test_line_diff.py
│   ├── test_char_diff.py
│   ├── test_pairing.py
│   ├── test_edge_cases.py
│   └── fixtures/
│
├── pyproject.toml
├── README.md
└── ...
```

The names are recommendations; the final repository structure should
follow the actual weekend tooling/specification if one is supplied.

------------------------------------------------------------------------

# 22. Separation of Responsibilities

## `myers.py`

Responsible only for:

``` text
sequence A
sequence B
    ↓
minimal edit script
```

It should not know about:

-   files,
-   colors,
-   terminal output,
-   GitHub,
-   Python source syntax.

------------------------------------------------------------------------

## `line_diff.py`

Responsible for:

``` text
file
 ↓
lines
 ↓
Myers
 ↓
line edits
```

------------------------------------------------------------------------

## `char_diff.py`

Responsible for:

``` text
old line
new line
 ↓
character sequences
 ↓
Myers
 ↓
character edits
```

------------------------------------------------------------------------

## `pairing.py`

Responsible for deciding how line-level replacement groups are passed to
character-level comparison.

------------------------------------------------------------------------

## `renderer.py`

Responsible for converting internal edit structures into the required
user-visible output.

------------------------------------------------------------------------

## `cli.py`

Responsible for:

-   argument parsing,
-   input validation,
-   file reading,
-   invoking the pipeline,
-   returning an exit status.

------------------------------------------------------------------------

# 23. CLI Design

Until the official weekend input/output specification is available, keep
the CLI thin.

A possible development interface is:

``` bash
python -m diff_engine file_a file_b
```

or:

``` bash
python -m diff_engine --part A file_a file_b
```

and:

``` bash
python -m diff_engine --part B file_a file_b
```

However, these are **development suggestions**, not requirements. The
actual command and output format should follow the official project
specification when provided.

------------------------------------------------------------------------

# 24. Testing Strategy

Testing is likely to be one of the most important parts of this project.

A diff implementation can appear correct on simple examples while
failing badly on repeated sequences or ambiguous shortest paths.

Testing should therefore occur at several levels.

------------------------------------------------------------------------

# 25. Unit Tests for Myers

Start with very small sequences.

## Empty sequences

``` text
A = []
B = []
```

Expected:

``` text
[]
```

## Insertion

``` text
A = ["a"]
B = ["a", "b"]
```

Expected:

``` text
EQUAL a
INSERT b
```

## Deletion

``` text
A = ["a", "b"]
B = ["a"]
```

Expected:

``` text
EQUAL a
DELETE b
```

## Replacement

``` text
A = ["a"]
B = ["b"]
```

A replacement is represented internally as:

``` text
DELETE a
INSERT b
```

because Myers' edit model consists of insertions and deletions, with
matches represented by diagonals.

------------------------------------------------------------------------

# 26. Repeated Elements

Repeated sequences are particularly important.

Test cases such as:

``` text
A = ["a", "a", "a"]
B = ["a", "a"]
```

and:

``` text
A = ["a", "b", "a"]
B = ["b", "a", "b"]
```

help expose incorrect diagonal handling and unstable tie-breaking.

------------------------------------------------------------------------

# 27. Already-Identical Files

If:

``` text
A == B
```

the result should contain only equality operations.

No unnecessary deletion or insertion should be produced.

This is an essential sanity test.

------------------------------------------------------------------------

# 28. Completely Different Files

Example:

``` text
A = ["a", "b", "c"]
B = ["x", "y", "z"]
```

The algorithm must still produce a valid minimal edit script.

------------------------------------------------------------------------

# 29. Large Common Prefix

Example:

``` text
A:
line1
line2
line3
...
line10000
old
```

``` text
B:
line1
line2
line3
...
line10000
new
```

This checks whether the algorithm efficiently handles long matching
regions.

------------------------------------------------------------------------

# 30. Large Common Suffix

Similarly test:

``` text
old
line1
line2
...
```

versus:

``` text
new
line1
line2
...
```

This exercises matching after the changed region.

------------------------------------------------------------------------

# 31. Character-Level Tests

Examples should include:

``` text
8000 → 8080
```

and:

``` text
foo → foo
```

and:

``` text
abc → xyz
```

and:

``` text
"" → "abc"
```

and:

``` text
abc → ""
```

Also test multiple separated changes within one line.

------------------------------------------------------------------------

# 32. Source-Code Tests

Create fixtures for:

### Python

``` python
def calculate(x):
    return x * 10
```

### Java

``` java
public int calculate(int x) {
    return x * 10;
}
```

### C++

``` cpp
int calculate(int x) {
    return x * 10;
}
```

Then introduce:

-   changed constants,
-   changed operators,
-   inserted lines,
-   removed lines,
-   changed indentation,
-   changed function calls.

The algorithm should not need to understand the language.

------------------------------------------------------------------------

# 33. Real-World Test Corpus

The project explicitly states that the tests are real and include source
files from actual open-source commits.

This is important because toy tests do not sufficiently validate the
implementation.

A real-world validation stage should include:

``` text
.txt
.py
.c
.cpp
.java
.ts
```

with:

-   small commits,
-   large commits,
-   many unchanged lines,
-   repeated blocks,
-   adjacent changes,
-   long lines,
-   formatting changes.

------------------------------------------------------------------------

# 34. Minimality Verification

Do not only verify that the output "looks right."

For small sequences, build a brute-force reference implementation that
enumerates possible edit scripts and determines the true minimum.

Then compare:

``` text
Myers edit count
        ==
brute-force minimum edit count
```

For example:

``` python
assert count_edits(myers(a, b)) == brute_force_minimum(a, b)
```

This is one of the strongest ways to validate the core algorithm.

Use brute force only for **small sequences** because its computational
cost grows rapidly.

------------------------------------------------------------------------

# 35. Important Invariants

Your implementation should satisfy invariants such as:

### Invariant 1

Applying the edit script to A must produce B.

``` text
apply(diff(A, B), A) == B
```

### Invariant 2

The edit count must be minimal.

``` text
edits(diff(A, B)) == minimum_possible_edits(A, B)
```

for testable small cases.

### Invariant 3

Identical inputs produce no edits.

``` text
diff(A, A) = equality only
```

### Invariant 4

Every output element must originate from either:

-   A,
-   B,
-   or an explicit equality between them.

------------------------------------------------------------------------

# 36. Newline Handling

Real source files introduce newline complications.

Examples:

``` text
LF   = \n
CRLF = \r\n
```

The implementation should establish a consistent policy for:

-   newline normalization,
-   final newline,
-   empty final lines,
-   files without a trailing newline.

Do not let newline behavior accidentally change the semantic line
sequence.

The final behavior should follow the official project specification when
provided.

------------------------------------------------------------------------

# 37. Unicode

Although the primary examples may be ASCII source code, text files can
contain Unicode.

Character-level comparison should therefore operate on Python strings
rather than assuming:

``` text
ASCII only
```

Test examples should include at least a few non-ASCII characters.

------------------------------------------------------------------------

# 38. Performance

Myers is attractive because it avoids exploring every possible edit
path.

The classic complexity is commonly expressed in terms of:

``` text
O((N + M)D)
```

where:

``` text
N = length of A
M = length of B
D = shortest edit distance
```

The practical performance is therefore especially favorable when the two
sequences are similar and `D` is relatively small.

For this project, correctness should be prioritized before aggressive
optimization.

------------------------------------------------------------------------

# 39. Memory Considerations

There are two related concerns:

1.  Finding the shortest edit path.
2.  Reconstructing the path.

A minimal implementation may store additional state/history to
reconstruct the actual sequence of operations.

The supplied notes also discuss the relationship between Myers'
algorithm and later approaches that reduce memory usage, including the
Hirschberg-style linear-space perspective.

For this project, do not prematurely optimize memory unless the actual
test limits require it.

------------------------------------------------------------------------

# 40. Part A and Part B Data Flow

The complete system can be modeled as:

``` text
             File A
               │
               ▼
        ┌──────────────┐
        │ Line Parser  │
        └──────┬───────┘
               │
               ▼
             Lines A
               │
               │
               │      Lines B
               │         ▲
               │         │
               │   ┌─────┴───────┐
               │   │ Line Parser │
               │   └─────────────┘
               │
               ▼
        ┌────────────────┐
        │  Myers Engine  │
        └───────┬────────┘
                │
                ▼
        Minimal Edit Script
                │
        ┌───────┴───────────┐
        │                   │
        ▼                   ▼
     Part A              Part B
        │                   │
        │             Changed lines
        │                   │
        │                   ▼
        │            Character Myers
        │                   │
        │                   ▼
        │            Character ranges
        │                   │
        └──────────┬────────┘
                   ▼
               Renderer
                   │
                   ▼
             CLI Output
```

------------------------------------------------------------------------

# 41. Agent-Assisted Development Strategy

Since the implementation will be heavily developed using AI coding
agents, the project should be divided into isolated tasks.

Do **not** initially give one agent the entire project.

Use incremental tasks.

------------------------------------------------------------------------

## Agent 1 --- Myers Core

Task:

``` text
Implement a generic Myers shortest edit script algorithm.

Requirements:
- sequence-to-sequence API
- insertion/deletion/equality representation
- deterministic behavior
- path reconstruction
- unit tests
- no file-system dependencies
- no language-specific logic
```

Deliverables:

``` text
myers.py
models.py
test_myers.py
```

------------------------------------------------------------------------

## Agent 2 --- Algorithm Adversarial Testing

Give it the implementation and ask it to find counterexamples.

Focus on:

``` text
empty sequences
repeated values
ambiguous matches
multiple shortest paths
large common prefixes
large common suffixes
completely different sequences
alternating sequences
```

Do not let this agent silently rewrite the algorithm. First make it
report failures.

------------------------------------------------------------------------

## Agent 3 --- Part A

Implement:

``` text
file → lines → Myers → line diff
```

It should consume the existing Myers API rather than duplicate it.

------------------------------------------------------------------------

## Agent 4 --- Character Diff

Implement:

``` text
old line + new line
        ↓
characters
        ↓
same Myers engine
        ↓
character operations
        ↓
highlight ranges
```

------------------------------------------------------------------------

## Agent 5 --- Integration

Connect:

``` text
CLI
 ↓
file reading
 ↓
line diff
 ↓
character diff
 ↓
renderer
```

------------------------------------------------------------------------

## Agent 6 --- QA

Run:

``` text
unit tests
integration tests
property tests
real source files
performance tests
```

and report failures separately.

------------------------------------------------------------------------

# 42. Recommended Development Order

Use this sequence:

``` text
Phase 1
Understand algorithm
        ↓
Phase 2
Define internal edit representation
        ↓
Phase 3
Implement Myers
        ↓
Phase 4
Prove/test minimality
        ↓
Phase 5
Build Part A
        ↓
Phase 6
Build character-level Myers
        ↓
Phase 7
Implement changed-character highlighting
        ↓
Phase 8
Build CLI
        ↓
Phase 9
Real-world testing
        ↓
Phase 10
Optimization and cleanup
```

Do not reverse this order by starting with UI/output formatting.

------------------------------------------------------------------------

# 43. Suggested Milestones

## Milestone 0 --- Specification

Deliver:

-   project requirements understood,
-   I/O contract identified,
-   internal representation designed.

------------------------------------------------------------------------

## Milestone 1 --- Myers Core

Definition of done:

``` text
Myers can transform any tested sequence A into B
and return a minimal edit script.
```

------------------------------------------------------------------------

## Milestone 2 --- Minimality Validation

Definition of done:

``` text
Small random sequences agree with brute-force minimum distance.
```

------------------------------------------------------------------------

## Milestone 3 --- Part A

Definition of done:

``` text
Two files produce the required minimal line diff.
```

------------------------------------------------------------------------

## Milestone 4 --- Part B

Definition of done:

``` text
Changed lines additionally expose precise changed-character regions.
```

------------------------------------------------------------------------

## Milestone 5 --- Integration

Definition of done:

``` text
One command runs the complete pipeline.
```

------------------------------------------------------------------------

## Milestone 6 --- Real Corpus

Definition of done:

``` text
The implementation works on realistic .txt/.py/.c/.cpp/.java/.ts files.
```

------------------------------------------------------------------------

# 44. Provisional Contracts and Open Decisions

Several sections defer to an official I/O specification that has not
been supplied yet. To let P-1..P-3 proceed without guessing silently,
the following **provisional defaults** apply. Each is isolated in one
module so it can be changed without touching the Myers core. Every item
marked OPEN must be confirmed or replaced when the official spec
arrives.

## 44.1 Tie-breaking (CONFIRMED by developer, 2026-10-02)

Use the classic Myers predecessor rule at every `(D, k)`:

``` text
if k == -D or (k != D and V[k - 1] < V[k + 1]):
    x = V[k + 1]        # step down from diagonal k+1  → INSERT
else:
    x = V[k - 1] + 1    # step right from diagonal k-1 → DELETE
```

Consequences:

-   output is fully deterministic (no randomness, no unordered
    iteration);
-   within a change region, deletions appear before insertions, which
    matches Git / GNU diff presentation;
-   regression oracle: the paper example `A = "ABCABBA"`,
    `B = "CBABAC"` must give `D = 5` and a fixed golden edit script.

## 44.2 Edit model (decided)

``` python
Operation = Literal["equal", "insert", "delete"]

@dataclass(frozen=True)
class Edit(Generic[T]):
    operation: Operation
    value: T
```

`myers_diff(a: Sequence[T], b: Sequence[T]) -> list[Edit[T]]`, where
`T` only needs `==`. The edit script is ordered so that reading
`equal` + `delete` values reproduces A, and `equal` + `insert` values
reproduces B.

## 44.3 Line splitting and newlines (OPEN, provisional default)

-   Files are read as bytes and decoded as UTF-8 (strict). A decode
    failure is a boundary error (exit code 2), not a silent replacement.
-   No universal-newline translation: lines are split on `\n` only.
    A `\r` before `\n` stays part of the line, so an LF↔CRLF change is
    reported as a change (same as Git without autocrlf).
-   `str.splitlines()` is **not** used, because it also splits on
    `\x0b`, `\x0c`, `\u2028`, etc., which would change the line sequence
    of real source files.
-   A trailing `\n` terminates the last line; it does not create an
    extra empty line. Whether each file ends with a newline is recorded
    separately and rendered as `\ No newline at end of file`.

## 44.4 Changed-line pairing (OPEN, provisional default)

A *change block* is a maximal run of non-equal edits between two equal
edits. With the tie-breaking rule above, each block is
`DELETE* INSERT*`. Pair the i-th deleted line with the i-th inserted
line; surplus lines are rendered as wholly deleted/inserted with no
character highlights. No similarity scoring.

## 44.5 Output format (OPEN, provisional default)

Part A, one line per edit:

``` text
  <line>    equal
- <line>    delete
+ <line>    insert
```

Part B, same layout, with changed character runs marked inline using
Git word-diff style markers, which are plain text and testable:

``` text
- timeout = 80[-0-]0
+ timeout = 80{+8+}0
```

Character ranges are half-open `[start, end)` indices into the line
(Python `str` code points, so Unicode is handled per code point).
ANSI colour output is not implemented unless the official spec asks for
it.

## 44.6 CLI and exit status (OPEN, provisional default)

``` bash
python -m diff_engine [--part {A,B}] FILE_A FILE_B
```

`--part` defaults to `B` (full pipeline). Exit codes follow diff(1):
`0` no differences, `1` differences found, `2` error (bad arguments,
missing/unreadable file, decode error). Errors go to stderr.

## 44.7 Memory (decided, revisit only on measurement)

Backtracking stores a snapshot of the live part of `V` (`2D + 1`
entries) after each `D`. Memory is `O(D²)`, acceptable for the expected
corpus. The linear-space (middle-snake) variant is implemented only if
a P-4 measurement shows a real file exceeding limits.

# 45. What You Should Personally Review

Even if AI agents write the implementation, you should manually
understand and review:

### Myers

-   `D`
-   `k`
-   `V[k]`
-   furthest-reaching point
-   diagonal/snake extension
-   termination condition
-   backtracking
-   tie-breaking

### Part A

-   line tokenization
-   edit grouping
-   output ordering

### Part B

-   changed-line pairing
-   character-level Myers
-   character-range extraction
-   highlight rendering

### Testing

-   minimality
-   reconstruction correctness
-   repeated sequences
-   empty files
-   newlines
-   real source files

------------------------------------------------------------------------

# 46. What Not to Let an AI Agent Do

Avoid giving an agent broad instructions such as:

> "Build a GitHub diff clone."

That encourages it to introduce unnecessary behavior.

Instead define precise contracts:

``` text
Input:
Sequence[T]

Output:
List[Edit[T]]

Guarantees:
1. Applying edits transforms A into B.
2. Edit count is minimal.
3. Output is deterministic.
4. No syntax knowledge is required.
```

Then build the next layer around that contract.

------------------------------------------------------------------------

# 47. Recommended Property Tests

Property-based testing can be extremely valuable.

For randomly generated small sequences:

``` python
A = random_sequence()
B = random_sequence()

edits = myers(A, B)

assert apply(edits, A) == B
```

Then compare the number of edits against a brute-force solver.

This gives two independent correctness checks:

``` text
Correct transformation
+
Minimal transformation
```

------------------------------------------------------------------------

# 48. Debugging the Myers Core

When a test fails, do not immediately inspect the final formatted diff.

Inspect the intermediate states:

``` text
D
k
V[k]
x
y
```

For example:

``` text
D = 2
k = 1
x = 5
y = 4
```

Then inspect:

``` text
A[x]
B[y]
```

and verify whether the diagonal extension is valid.

For path reconstruction, inspect the sequence of coordinates:

``` text
(0,0)
(1,0)
(2,1)
(3,2)
...
```

This is far easier than debugging a rendered terminal output.

------------------------------------------------------------------------

# 49. Debugging Architecture

Use a pipeline where every stage can be inspected:

``` text
INPUT
  ↓
TOKENS
  ↓
MYERS EDITS
  ↓
GROUPED LINE EDITS
  ↓
CHARACTER EDITS
  ↓
RENDERED OUTPUT
```

If the final output is wrong, identify the first stage where the data
becomes wrong.

------------------------------------------------------------------------

# 50. Important Risk Areas

The highest-risk areas are:

## Risk 1 --- Incorrect backtracking

The forward search may find the correct edit distance while
reconstruction produces the wrong operations.

## Risk 2 --- Non-minimal output

The result may look correct but contain unnecessary edits.

## Risk 3 --- Tie-breaking

Multiple shortest paths can produce different valid scripts.

## Risk 4 --- Repeated lines

Repeated sequences can expose incorrect matching decisions.

## Risk 5 --- Changed-line pairing

Part B needs a clear policy for pairing deleted and inserted lines.

## Risk 6 --- Newline semantics

Real files may differ in final-newline and CRLF/LF behavior.

## Risk 7 --- Performance

Large files can expose inefficient implementations.

## Risk 8 --- Agent overengineering

An AI agent may introduce unnecessary abstractions or replace the
intended algorithm with a library call.

For this project, the Myers implementation itself should remain explicit
and reviewable.

------------------------------------------------------------------------

# 51. Validation Checklist

Before declaring the project complete:

## Algorithm

-   [ ] Myers is implemented directly.
-   [ ] Shortest edit script is produced.
-   [ ] Diagonal processing is correct.
-   [ ] Path reconstruction is correct.
-   [ ] Tie-breaking is deterministic.
-   [ ] No hidden use of an external diff library replaces the
    algorithm.

## Part A

-   [ ] Files are read correctly.
-   [ ] Lines are represented consistently.
-   [ ] Insertions work.
-   [ ] Deletions work.
-   [ ] Replacements work.
-   [ ] Unchanged regions are preserved.
-   [ ] Output is minimal.

## Part B

-   [ ] Changed lines are identified from Part A.
-   [ ] Character-level Myers is reused.
-   [ ] Changed character ranges are correct.
-   [ ] Multiple character changes work.
-   [ ] Empty strings work.
-   [ ] Long lines work.

## Real files

-   [ ] `.txt`
-   [ ] `.py`
-   [ ] `.c`
-   [ ] `.cpp`
-   [ ] `.java`
-   [ ] `.ts`

## Edge cases

-   [ ] Empty file → empty file
-   [ ] Empty → non-empty
-   [ ] Non-empty → empty
-   [ ] Identical files
-   [ ] Completely different files
-   [ ] Repeated lines
-   [ ] Repeated characters
-   [ ] Large common prefix
-   [ ] Large common suffix
-   [ ] No trailing newline
-   [ ] CRLF/LF behavior
-   [ ] Unicode

## Quality

-   [ ] Unit tests
-   [ ] Integration tests
-   [ ] Property tests
-   [ ] Brute-force minimality checks for small inputs
-   [ ] Real-world corpus tests
-   [ ] Performance checks
-   [ ] Clean CLI
-   [ ] Documentation

------------------------------------------------------------------------

# 52. Final Mental Model

The entire project can be reduced to one idea:

``` text
A sequence
    +
B sequence
    ↓
Find the shortest path through the edit graph
    ↓
Recover the path
    ↓
Convert path to:
    EQUAL / DELETE / INSERT
    ↓
Part A:
    render line changes
    ↓
Part B:
    take changed line pairs
    ↓
    run the same Myers algorithm on characters
    ↓
    identify changed character ranges
    ↓
    render highlights
```

The key conceptual relationship is:

``` text
                  SAME ALGORITHM
                       │
          ┌────────────┴────────────┐
          │                         │
       Lines                     Characters
          │                         │
          ▼                         ▼
       Part A                     Part B
```

That is the cleanest way to think about the system.

------------------------------------------------------------------------

# 53. Final Recommended Project Strategy

Because you already understand the internal working of Myers, the next
step should **not** be to immediately ask an agent to generate the
entire application.

Instead:

``` text
1. Freeze the algorithm contract.
2. Implement/test Myers independently.
3. Prove minimality on small sequences.
4. Build line diff around it.
5. Build character diff by reusing it.
6. Add the renderer.
7. Add the CLI.
8. Test against real source files.
9. Stress-test edge cases.
10. Only then optimize.
```

The most important architectural principle is:

> **Myers should be the reusable mathematical core; file handling, line
> processing, character highlighting, and rendering should remain
> separate layers.**

This gives you a system that is easier for AI agents to implement
incrementally, easier for you to review, and much easier to debug when a
real-world test fails.

------------------------------------------------------------------------

# 54. Reference to the Supplied Myers Notes

The supplied 19-page notes are the primary algorithmic reference for
this document. In particular, they cover:

-   the shortest-edit-script formulation,
-   the edit graph,
-   diagonal movement and the `k = x - y` representation,
-   furthest-reaching paths,
-   converting the result into an edit script,
-   behavior when multiple shortest scripts exist,
-   the relationship between Myers and later memory-oriented approaches,
-   Git's use of diff/merge concepts.

The notes also place the algorithm in the broader context of Git's diff
engine and three-way merging.

For this project, the implementation should follow the official project
specification for exact CLI arguments, output formatting, tie-breaking
requirements, and evaluation constraints once those details are
provided.
