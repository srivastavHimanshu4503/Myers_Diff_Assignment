import random

import pytest

from diff_engine.myers import _forward_trace
from oracles import minimum_edit_distance


def test_golden_trace_for_myers_paper_example():
    # Myers' 1986 paper, "ABCABBA" -> "CBABAC".
    # D = 5: delete A at 0, delete B at 2, insert C at end,
    #        delete B at 5, insert A at 4 (various equivalent scripts exist).
    # With the D1 tie-breaking rule (deletions first), the trace is
    # deterministic and was computed by hand for this test.
    a = "ABCABBA"
    b = "CBABAC"
    trace = _forward_trace(a, b)

    # D = 5, so 5 saved rounds (0..4).
    assert len(trace) == 5

    # Hand-computed furthest-x values at each (d, k).
    # Round 0: k=0: x=0 (starting point).
    assert trace[0] == [0]
    # Round 1: k=−1: x=0, k=1: x=1.
    assert trace[1] == [0, 1]
    # Round 2: k=−2: x=2 (from k=−1, right+snake), k=0: x=2, k=2: x=3.
    assert trace[2] == [2, 2, 3]
    # Round 3: k=−3: x=3, k=−1: x=4 (tie at x=2, chose DELETE), k=1: x=5, k=3: x=5.
    # The k=−1 tie (predecessors both at x=2) is where the D1 rule matters.
    assert trace[3] == [3, 4, 5, 5]
    # Round 4: k=−4: x=3, k=−2: x=4, k=0: x=5,
    #          k=2: x=7 (tie at x=5, chose DELETE, then 2-step snake),
    #          k=4: x=7.
    # The k=2 tie is the second place where the D1 rule applies.
    assert trace[4] == [3, 4, 5, 7, 7]
    # Round 5 reaches (7, 6) at k=1, so the search stops and round 5 is
    # not saved.


@pytest.mark.parametrize(
    ("a", "b", "expected_d"),
    [
        # Empty and identical cases.
        ([], [], 0),
        ("", "", 0),
        ("abc", "abc", 0),
        (["a", "b", "c"], ["a", "b", "c"], 0),
        # Single insertion.
        (["a"], ["a", "b"], 1),
        ("a", "ab", 1),
        # Single deletion.
        (["a", "b"], ["a"], 1),
        ("ab", "a", 1),
        # Replacement (= one delete + one insert).
        (["a"], ["b"], 2),
        ("a", "b", 2),
        # Repeated elements.
        ("aaa", "aa", 1),
        ("aba", "bab", 2),
        # Completely different.
        ("abc", "xyz", 6),
        # Large common prefix.
        (["line"] * 10000 + ["old"], ["line"] * 10000 + ["new"], 2),
        # Large common suffix.
        (["old"] + ["line"] * 10000, ["new"] + ["line"] * 10000, 2),
    ],
)
def test_forward_trace_d_equals_oracle(a, b, expected_d):
    trace = _forward_trace(a, b)
    assert len(trace) == expected_d
    assert len(trace) == minimum_edit_distance(a, b)


def test_forward_trace_on_random_pairs_agrees_with_oracle():
    rng = random.Random(0)
    for _ in range(2000):
        alphabet_size = rng.randint(1, 4)
        alphabet = "abcd"[:alphabet_size]
        a = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
        b = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
        trace = _forward_trace(a, b)
        assert len(trace) == minimum_edit_distance(a, b), (a, b)


def test_forward_trace_snapshot_shape():
    # Round d saves d+1 values (for diagonals −d, −d+2, …, d).
    trace = _forward_trace("abc", "ab")
    assert len(trace) == 1  # D = 1
    assert len(trace[0]) == 1  # round 0: 1 diagonal


def test_forward_trace_round_zero_reflects_shared_prefix():
    # Round 0 follows the initial shared diagonal as far as possible.
    trace = _forward_trace("aabcx", "aabcy")
    assert len(trace) == 2  # D = 2 (delete x, insert y)
    # Round 0 diagonal k=0 reaches x=4 (shared "aabc").
    assert trace[0] == [4]


def test_forward_trace_accepts_str_and_list():
    # The algorithm is generic over sequences with ==.
    trace_str = _forward_trace("abc", "ac")
    trace_list = _forward_trace(["a", "b", "c"], ["a", "c"])
    assert trace_str == trace_list
