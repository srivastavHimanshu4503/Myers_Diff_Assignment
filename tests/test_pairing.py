import pytest

from diff_engine.line_diff import Block
from diff_engine.pairing import pair_block


def test_pair_block_one_to_one():
    block = Block(equal_lines=[], deleted_lines=["old"], inserted_lines=["new"])
    pairs, unpaired_del, unpaired_ins = pair_block(block)
    assert pairs == [("old", "new")]
    assert unpaired_del == []
    assert unpaired_ins == []


def test_pair_block_two_to_two():
    block = Block(
        equal_lines=[],
        deleted_lines=["old1", "old2"],
        inserted_lines=["new1", "new2"],
    )
    pairs, unpaired_del, unpaired_ins = pair_block(block)
    assert pairs == [("old1", "new1"), ("old2", "new2")]
    assert unpaired_del == []
    assert unpaired_ins == []


def test_pair_block_three_to_one():
    block = Block(
        equal_lines=[],
        deleted_lines=["old1", "old2", "old3"],
        inserted_lines=["new1"],
    )
    pairs, unpaired_del, unpaired_ins = pair_block(block)
    assert pairs == [("old1", "new1")]
    assert unpaired_del == ["old2", "old3"]
    assert unpaired_ins == []


def test_pair_block_zero_to_two():
    block = Block(
        equal_lines=[],
        deleted_lines=[],
        inserted_lines=["new1", "new2"],
    )
    pairs, unpaired_del, unpaired_ins = pair_block(block)
    assert pairs == []
    assert unpaired_del == []
    assert unpaired_ins == ["new1", "new2"]


def test_pair_block_two_to_zero():
    block = Block(
        equal_lines=[],
        deleted_lines=["old1", "old2"],
        inserted_lines=[],
    )
    pairs, unpaired_del, unpaired_ins = pair_block(block)
    assert pairs == []
    assert unpaired_del == ["old1", "old2"]
    assert unpaired_ins == []
