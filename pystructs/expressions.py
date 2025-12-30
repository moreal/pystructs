"""Expression system for validation and computation."""

from __future__ import annotations

import binascii
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "Expression",
    "Len",
    "Value",
    "Const",
    "Checksum",
    "BinaryOp",
)


class Expression(ABC):
    """Abstract base class for expressions.

    Expressions are used in validators to compute expected values.
    """

    @abstractmethod
    def evaluate(self, instance: Struct) -> Any:
        """Evaluate the expression.

        Args:
            instance: The struct instance to evaluate against

        Returns:
            The computed value
        """
        pass

    def __add__(self, other: Expression | Any) -> BinaryOp:
        """Add two expressions."""
        return BinaryOp(self, "+", other)

    def __radd__(self, other: Any) -> BinaryOp:
        """Add with expression on the right."""
        return BinaryOp(Const(other), "+", self)

    def __sub__(self, other: Expression | Any) -> BinaryOp:
        """Subtract two expressions."""
        return BinaryOp(self, "-", other)

    def __rsub__(self, other: Any) -> BinaryOp:
        """Subtract with expression on the right."""
        return BinaryOp(Const(other), "-", self)

    def __mul__(self, other: Expression | Any) -> BinaryOp:
        """Multiply two expressions."""
        return BinaryOp(self, "*", other)

    def __rmul__(self, other: Any) -> BinaryOp:
        """Multiply with expression on the right."""
        return BinaryOp(Const(other), "*", self)

    def __truediv__(self, other: Expression | Any) -> BinaryOp:
        """Divide two expressions."""
        return BinaryOp(self, "/", other)


class Len(Expression):
    """Length of a field's value.

    Examples:
        >>> Consistency('payload_size', equals=Len('payload'))
    """

    def __init__(self, field: str):
        """Initialize a Len expression.

        Args:
            field: Field name to get length of
        """
        self.field = field

    def evaluate(self, instance: Struct) -> int:
        """Get the length of the field value.

        Args:
            instance: The struct instance

        Returns:
            Length of the field value
        """
        value = getattr(instance, self.field)
        return len(value)

    def __repr__(self) -> str:
        return f"Len({self.field!r})"


class Value(Expression):
    """Value of a field.

    Examples:
        >>> Consistency('checksum', equals=Value('expected_checksum'))
    """

    def __init__(self, field: str):
        """Initialize a Value expression.

        Args:
            field: Field name to get value of
        """
        self.field = field

    def evaluate(self, instance: Struct) -> Any:
        """Get the field value.

        Args:
            instance: The struct instance

        Returns:
            The field value
        """
        return getattr(instance, self.field)

    def __repr__(self) -> str:
        return f"Value({self.field!r})"


class Const(Expression):
    """Constant value.

    Examples:
        >>> Consistency('magic', equals=Const(0xDEADBEEF))
    """

    def __init__(self, value: Any):
        """Initialize a Const expression.

        Args:
            value: The constant value
        """
        self.value = value

    def evaluate(self, instance: Struct) -> Any:
        """Return the constant value.

        Args:
            instance: The struct instance (unused)

        Returns:
            The constant value
        """
        return self.value

    def __repr__(self) -> str:
        return f"Const({self.value!r})"


class Checksum(Expression):
    """Checksum of a field's value.

    Supported algorithms: 'crc32'

    Examples:
        >>> Consistency('checksum', equals=Checksum('payload', 'crc32'))
    """

    def __init__(self, field: str, algorithm: str = "crc32"):
        """Initialize a Checksum expression.

        Args:
            field: Field name to compute checksum of
            algorithm: Checksum algorithm ('crc32')
        """
        self.field = field
        self.algorithm = algorithm

    def evaluate(self, instance: Struct) -> int:
        """Compute the checksum of the field value.

        Args:
            instance: The struct instance

        Returns:
            The checksum value

        Raises:
            ValueError: If algorithm is not supported
        """
        data = getattr(instance, self.field)
        if isinstance(data, str):
            data = data.encode("utf-8")

        if self.algorithm == "crc32":
            return binascii.crc32(data) & 0xFFFFFFFF
        else:
            raise ValueError(f"Unknown checksum algorithm: {self.algorithm}")

    def __repr__(self) -> str:
        return f"Checksum({self.field!r}, {self.algorithm!r})"


class BinaryOp(Expression):
    """Binary operation between two expressions.

    Examples:
        >>> Consistency('total_size', equals=Len('header') + Len('payload'))
    """

    def __init__(self, left: Expression, op: str, right: Expression | Any):
        """Initialize a BinaryOp expression.

        Args:
            left: Left operand (Expression)
            op: Operator ('+', '-', '*', '/')
            right: Right operand (Expression or value)
        """
        self.left = left
        self.op = op
        self.right = right if isinstance(right, Expression) else Const(right)

    def evaluate(self, instance: Struct) -> Any:
        """Evaluate the binary operation.

        Args:
            instance: The struct instance

        Returns:
            The result of the operation
        """
        left_val = self.left.evaluate(instance)
        right_val = self.right.evaluate(instance)

        if self.op == "+":
            return left_val + right_val
        elif self.op == "-":
            return left_val - right_val
        elif self.op == "*":
            return left_val * right_val
        elif self.op == "/":
            return left_val / right_val
        else:
            raise ValueError(f"Unknown operator: {self.op}")

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"
