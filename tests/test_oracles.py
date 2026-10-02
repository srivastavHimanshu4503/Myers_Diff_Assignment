import random
from itertools import combinations

import pytest

from diff_engine.models import Edit
from oracles import lcs_length, minimum_edit_distance, replay


def _is_subsequence(candidate, sequence) -> bool:
    remaining = iter(sequence)
    # `in` on an iterator consumes it up to the match, which enforces order.
    return all(item in remaining for item in candidate)


def brute_force_lcs_length(a, b) -> int:
    """Longest subsequence of A that is also a subsequence of B.

    Enumerates subsets of A's positions from longest to shortest, so it
    shares no logic with the dynamic-programming oracle it validates.
    """
    for length in range(len(a), -1, -1):
        for positions in combinations(range(len(a)), length):
            if _is_subsequence([a[i] for i in positions], b):
                return length
    raise AssertionError("unreachable: the empty subsequence always matches")


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("", "", 0),
        ("abc", "abc", 0),
        ("abc", "xyz", 6),
        ("", "abc", 3),
        ("abc", "", 3),
        ("aaa", "aa", 1),
        ("aba", "bab", 2),
        ("ABCABBA", "CBABAC", 5),  # Myers' paper example
    ],
)
def test_minimum_edit_distance_hand_computed(a, b, expected):
    assert minimum_edit_distance(a, b) == expected


def test_minimum_edit_distance_on_lines():
    a = ["a", "b", "c", "d"]
    b = ["a", "b", "X", "c", "d"]
    assert minimum_edit_distance(a, b) == 1


def test_lcs_length_matches_brute_force_on_random_pairs():
    rng = random.Random(0)
    for case in range(500):
        alphabet = "ab" if case % 2 == 0 else "abc"
        a = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))
        b = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))
        assert lcs_length(a, b) == brute_force_lcs_length(a, b), (a, b)


def test_replay_rebuilds_both_sequences():
    edits = [
        Edit("equal", "def add(a, b):"),
        Edit("delete", "    return a + b"),
        Edit("insert", "    return a + b + 1"),
        Edit("equal", ""),
    ]
    assert replay(edits) == (
        ["def add(a, b):", "    return a + b", ""],
        ["def add(a, b):", "    return a + b + 1", ""],
    )


def test_replay_of_empty_script_is_empty():
    assert replay([]) == ([], [])
