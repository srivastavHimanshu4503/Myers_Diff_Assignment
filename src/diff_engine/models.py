"""Shared edit representation produced by the Myers core."""

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

T = TypeVar("T")

Operation = Literal["equal", "insert", "delete"]

_OPERATIONS = frozenset(("equal", "insert", "delete"))


@dataclass(frozen=True)
class Edit(Generic[T]):
    """One step of an edit script transforming sequence A into sequence B.

    ``equal`` and ``delete`` values come from A, ``equal`` and ``insert``
    values come from B. ``T`` only needs to support ``==``, so the same type
    serves line-level and character-level diffs.
    """

    operation: Operation
    value: T

    def __post_init__(self) -> None:
        # Literal is not enforced at runtime; reject impossible states here
        # instead of letting a bad edit reach replay or the renderer.
        if self.operation not in _OPERATIONS:
            raise ValueError(f"invalid edit operation: {self.operation!r}")
