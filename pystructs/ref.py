"""Reference system for field cross-references."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "Ref",
    "RefComparison",
    "RefLogical",
)


class Ref:
    """Reference to another field's value.

    Ref allows fields to reference other fields' current values. This is used
    for variable-length fields and conditional logic.

    Path formats:
        - 'field_name': Same level field
        - 'nested.field': Nested struct field (dot notation)
        - '../field_name': Parent struct field
        - '/header/size': Absolute path from root

    Examples:
        >>> payload = Bytes(size=Ref('payload_size'))
        >>> data = Bytes(size=Ref('header.data_size'))
        >>> item_data = Bytes(size=Ref('../item_size'))
    """

    def __init__(self, path: str):
        """Initialize a field reference.

        Args:
            path: Path to the field to reference
        """
        self.path = path

    def resolve(self, instance: Struct) -> Any:
        """Resolve the reference to get the actual value.

        Args:
            instance: The struct instance to resolve from

        Returns:
            The value of the referenced field
        """
        if self.path.startswith("/"):
            # Absolute path: start from root
            target = instance._root
            parts = self.path[1:].split("/")
        elif self.path.startswith("../"):
            # Relative path: navigate to parent
            target = instance
            parts = self.path.split("/")
            while parts and parts[0] == "..":
                if target._parent is None:
                    raise ValueError(f"Cannot resolve '../' - no parent for {target}")
                target = target._parent
                parts.pop(0)
        else:
            # Current level: use dot notation
            target = instance
            parts = self.path.split(".")

        for part in parts:
            if not part:
                continue
            target = getattr(target, part)

        return target

    def __repr__(self) -> str:
        return f"Ref({self.path!r})"

    # Comparison operators for use in Conditional
    def __eq__(self, other: Any) -> RefComparison:  # type: ignore[override]
        return RefComparison(self, "==", other)

    def __ne__(self, other: Any) -> RefComparison:  # type: ignore[override]
        return RefComparison(self, "!=", other)

    def __lt__(self, other: Any) -> RefComparison:
        return RefComparison(self, "<", other)

    def __le__(self, other: Any) -> RefComparison:
        return RefComparison(self, "<=", other)

    def __gt__(self, other: Any) -> RefComparison:
        return RefComparison(self, ">", other)

    def __ge__(self, other: Any) -> RefComparison:
        return RefComparison(self, ">=", other)


class RefComparison:
    """Result of comparing a Ref with a value.

    Used in Conditional fields to determine if a field should exist.

    Examples:
        >>> extra = Conditional(UInt32(), when=Ref('version') >= 2)
    """

    def __init__(self, ref: Ref, op: str, value: Any):
        """Initialize a reference comparison.

        Args:
            ref: The reference to compare
            op: The comparison operator ('==', '!=', '<', '<=', '>', '>=')
            value: The value to compare against
        """
        self.ref = ref
        self.op = op
        self.value = value

    def evaluate(self, instance: Struct) -> bool:
        """Evaluate the comparison.

        Args:
            instance: The struct instance to evaluate against

        Returns:
            True if the comparison is satisfied
        """
        resolved = self.ref.resolve(instance)

        if self.op == "==":
            return resolved == self.value
        elif self.op == "!=":
            return resolved != self.value
        elif self.op == "<":
            return resolved < self.value
        elif self.op == "<=":
            return resolved <= self.value
        elif self.op == ">":
            return resolved > self.value
        elif self.op == ">=":
            return resolved >= self.value
        else:
            raise ValueError(f"Unknown operator: {self.op}")

    def __repr__(self) -> str:
        return f"RefComparison({self.ref!r} {self.op} {self.value!r})"

    # Logical operators for combining comparisons
    def __and__(self, other: RefComparison) -> RefLogical:
        return RefLogical(self, "and", other)

    def __or__(self, other: RefComparison) -> RefLogical:
        return RefLogical(self, "or", other)


class RefLogical:
    """Logical combination of RefComparison objects.

    Examples:
        >>> cond = (Ref('version') >= 2) & (Ref('flags') != 0)
        >>> field = Conditional(UInt32(), when=cond)
    """

    def __init__(
        self,
        left: RefComparison | RefLogical,
        op: str,
        right: RefComparison | RefLogical,
    ):
        self.left = left
        self.op = op
        self.right = right

    def evaluate(self, instance: Struct) -> bool:
        """Evaluate the logical expression.

        Args:
            instance: The struct instance to evaluate against

        Returns:
            True if the logical expression is satisfied
        """
        left_result = self.left.evaluate(instance)
        right_result = self.right.evaluate(instance)

        if self.op == "and":
            return left_result and right_result
        elif self.op == "or":
            return left_result or right_result
        else:
            raise ValueError(f"Unknown logical operator: {self.op}")

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"

    def __and__(self, other: RefComparison | RefLogical) -> RefLogical:
        return RefLogical(self, "and", other)

    def __or__(self, other: RefComparison | RefLogical) -> RefLogical:
        return RefLogical(self, "or", other)
