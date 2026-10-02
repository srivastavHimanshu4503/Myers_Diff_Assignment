"""Adversarial test suite for Myers core (P1.5).

Hunts counterexamples: empty, repeated, alternating, ambiguous, large
prefix/suffix, fully different, alphabet size 1. Each test checks replay
and minimality invariants.
"""
import pytest
from diff_engine.myers import myers_diff
from oracles import replay, minimum_edit_distance


def count_edits(edits) -> int:
    return sum(1 for e in edits if e.operation != "equal")


@pytest.mark.parametrize(
    ("a", "b", "description"),
    [
        # Empty sequences.
        ("", "", "both empty"),
        ("", "a", "empty to single"),
        ("a", "", "single to empty"),
        ("", "abc", "empty to multiple"),
        ("abc", "", "multiple to empty"),
        # Heavy repetition (alphabet size 1).
        ("a", "a", "same single char"),
        ("aa", "aa", "same two chars"),
        ("aaa", "aaa", "same three chars"),
        ("a", "aa", "one to two same"),
        ("aa", "a", "two to one same"),
        ("aaa", "aa", "three to two same (spec §26)"),
        ("aa", "aaa", "two to three same"),
        ("aaaa", "aa", "four to two same"),
        ("aa", "aaaa", "two to four same"),
        ("aaaaa", "a", "five to one same"),
        ("a", "aaaaa", "one to five same"),
        ("a" * 100, "a" * 99, "100 to 99 same"),
        ("a" * 99, "a" * 100, "99 to 100 same"),
        # Alternating sequences.
        ("ab", "ba", "swap two"),
        ("aba", "bab", "alternating 3 (spec §26)"),
        ("abab", "baba", "alternating 4"),
        ("ababab", "bababa", "alternating 6"),
        ("abcabc", "bcabca", "alternating 6 with 3 chars"),
        # Repeated blocks.
        ("abab", "ab", "repeated to single"),
        ("ab", "abab", "single to repeated"),
        ("abcabc", "abc", "triple block to single"),
        ("abc", "abcabc", "single to triple block"),
        ("xyxyxy", "yxyxyx", "shifted repeated block"),
        # Ambiguous matches (multiple shortest paths possible).
        ("aa", "bb", "two same to two different"),
        ("aaa", "bbb", "three same to three different"),
        ("ab", "cd", "two different to two different"),
        ("abc", "def", "three different to three different"),
        ("aabb", "bbaa", "two pairs swapped"),
        ("abba", "baab", "palindromes"),
        # Fully different (no common elements).
        ("a", "b", "single different"),
        ("ab", "cd", "two different"),
        ("abc", "xyz", "three different (spec §26)"),
        ("abcd", "wxyz", "four different"),
        ("abcde", "vwxyz", "five different"),
        # Large common prefix.
        ("x" * 10000 + "a", "x" * 10000 + "b", "10k prefix + diff"),
        ("x" * 5000 + "old", "x" * 5000 + "new", "5k prefix + diff"),
        # Large common suffix.
        ("a" + "x" * 10000, "b" + "x" * 10000, "diff + 10k suffix"),
        ("old" + "x" * 5000, "new" + "x" * 5000, "diff + 5k suffix"),
        # Both large prefix and suffix.
        ("x" * 1000 + "a" + "y" * 1000, "x" * 1000 + "b" + "y" * 1000, "1k prefix + diff + 1k suffix"),
        # Mixed: common prefix, different middle, common suffix.
        ("abc_old_xyz", "abc_new_xyz", "mixed common regions"),
        # Edge: all elements match but different order.
        ("abc", "bca", "permutation 1"),
        ("abc", "cab", "permutation 2"),
        ("abc", "cba", "reverse"),
        # Single insertion/deletion in various positions.
        ("abc", "abXc", "insert middle"),
        ("abXc", "abc", "delete middle"),
        ("abc", "Xabc", "insert start"),
        ("Xabc", "abc", "delete start"),
        ("abc", "abcX", "insert end"),
        ("abcX", "abc", "delete end"),
    ],
)
def test_adversarial_cases(a, b, description):
    """Check replay and minimality invariants on adversarial inputs."""
    edits = myers_diff(a, b)
    
    # Replay must reconstruct original sequences.
    ra, rb = replay(edits)
    assert (ra, rb) == (list(a), list(b)), f"Replay failed for {description}: {a!r} -> {b!r}"
    
    # Edit count must equal the true minimum.
    assert count_edits(edits) == minimum_edit_distance(a, b), \
        f"Non-minimal for {description}: {a!r} -> {b!r}"


def test_adversarial_list_inputs():
    """Same adversarial cases but with list inputs instead of strings."""
    test_cases = [
        ([], []),
        (["a"], []),
        ([], ["a"]),
        (["a", "a", "a"], ["a", "a"]),
        (["a", "b", "a"], ["b", "a", "b"]),
        (["x"] * 1000 + ["a"], ["x"] * 1000 + ["b"]),
    ]
    for a, b in test_cases:
        edits = myers_diff(a, b)
        ra, rb = replay(edits)
        assert (ra, rb) == (a, b), f"Replay failed for list input: {a!r} -> {b!r}"
        assert count_edits(edits) == minimum_edit_distance(a, b), \
            f"Non-minimal for list input: {a!r} -> {b!r}"


def test_adversarial_determinism_on_ambiguous_cases():
    """Cases with multiple shortest paths must still be deterministic."""
    ambiguous_cases = [
        ("aa", "bb"),
        ("aaa", "bbb"),
        ("aabb", "bbaa"),
        ("abba", "baab"),
    ]
    for a, b in ambiguous_cases:
        edits1 = myers_diff(a, b)
        edits2 = myers_diff(a, b)
        assert edits1 == edits2, f"Non-deterministic for {a!r} -> {b!r}"
