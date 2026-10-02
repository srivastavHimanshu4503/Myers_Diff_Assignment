import dataclasses

import pytest

from diff_engine.models import Edit


def test_edit_stores_operation_and_value():
    edit = Edit("delete", "    return a + b")
    assert edit.operation == "delete"
    assert edit.value == "    return a + b"


def test_edits_with_same_fields_are_equal_and_hash_equal():
    # Golden-script tests compare whole lists of edits, which relies on
    # value equality rather than identity.
    assert Edit("equal", "a") == Edit("equal", "a")
    assert hash(Edit("equal", "a")) == hash(Edit("equal", "a"))
    assert Edit("equal", "a") != Edit("insert", "a")
    assert Edit("equal", "a") != Edit("equal", "b")


def test_edit_is_immutable():
    edit = Edit("insert", "x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        edit.operation = "delete"


@pytest.mark.parametrize("operation", ["replace", "EQUAL", "", None])
def test_invalid_operation_is_rejected(operation):
    with pytest.raises(ValueError, match="invalid edit operation"):
        Edit(operation, "x")
