"""Validation system for pystructs."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, List

from pystructs.exceptions import InconsistencyError, ValidationError
from pystructs.expressions import Expression

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "Validator",
    "FieldValidator",
    "Range",
    "OneOf",
    "Regex",
    "BytePattern",
    "Consistency",
    "Custom",
)


class Validator(ABC):
    """Abstract base class for struct-level validators.

    Validators are run when validate() is called on a struct.
    """

    @abstractmethod
    def validate(self, instance: Struct) -> None:
        """Validate the struct instance.

        Args:
            instance: The struct instance to validate

        Raises:
            ValidationError: If validation fails
        """
        pass


class FieldValidator(ABC):
    """Abstract base class for field-level validators.

    Field validators are run for individual field values.
    """

    @abstractmethod
    def __call__(self, value: Any, instance: Struct) -> None:
        """Validate a field value.

        Args:
            value: The field value to validate
            instance: The struct instance (for cross-field validation)

        Raises:
            ValidationError: If validation fails
        """
        pass


# === Field-level validators ===


class Range(FieldValidator):
    """Validate that a numeric value is within a range.

    Examples:
        >>> version = UInt8(validators=[Range(1, 10)])
    """

    def __init__(self, min_val: float | None = None, max_val: float | None = None):
        """Initialize a Range validator.

        Args:
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)
        """
        self.min_val = min_val
        self.max_val = max_val

    def __call__(self, value: Any, instance: Struct) -> None:
        if self.min_val is not None and value < self.min_val:
            raise ValidationError(f"Value {value} is less than minimum {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValidationError(
                f"Value {value} is greater than maximum {self.max_val}"
            )

    def __repr__(self) -> str:
        return f"Range({self.min_val}, {self.max_val})"


class OneOf(FieldValidator):
    """Validate that a value is one of allowed choices.

    Examples:
        >>> msg_type = UInt8(validators=[OneOf([1, 2, 3])])
    """

    def __init__(self, choices: List[Any]):
        """Initialize a OneOf validator.

        Args:
            choices: List of allowed values
        """
        self.choices = choices

    def __call__(self, value: Any, instance: Struct) -> None:
        if value not in self.choices:
            raise ValidationError(
                f"Value {value} is not in allowed choices {self.choices}"
            )

    def __repr__(self) -> str:
        return f"OneOf({self.choices!r})"


class Regex(FieldValidator):
    """Validate that a string matches a regex pattern.

    Examples:
        >>> name = String(length=10, validators=[Regex(r'^[a-zA-Z]+$')])
    """

    def __init__(self, pattern: str):
        """Initialize a Regex validator.

        Args:
            pattern: Regular expression pattern
        """
        self.pattern = re.compile(pattern)

    def __call__(self, value: Any, instance: Struct) -> None:
        if not self.pattern.match(value):
            raise ValidationError(
                f"Value '{value}' does not match pattern {self.pattern.pattern}"
            )

    def __repr__(self) -> str:
        return f"Regex({self.pattern.pattern!r})"


class BytePattern(FieldValidator):
    """Validate that bytes start with a specific pattern.

    Examples:
        >>> magic = FixedBytes(4, validators=[BytePattern(b'\\x89PNG')])
    """

    def __init__(self, pattern: bytes):
        """Initialize a BytePattern validator.

        Args:
            pattern: Expected byte pattern at start
        """
        self.pattern = pattern

    def __call__(self, value: Any, instance: Struct) -> None:
        if not value.startswith(self.pattern):
            raise ValidationError(
                f"Bytes do not start with expected pattern {self.pattern!r}"
            )

    def __repr__(self) -> str:
        return f"BytePattern({self.pattern!r})"


# === Struct-level validators ===


class Consistency(Validator):
    """Validate consistency between fields.

    Compares a field's value against an expression.

    Examples:
        >>> class Packet(Struct):
        ...     class Meta:
        ...         validators = [
        ...             Consistency('payload_size', equals=Len('payload')),
        ...             Consistency('checksum', equals=Checksum('payload', 'crc32')),
        ...         ]
    """

    def __init__(
        self,
        field: str,
        equals: Expression | None = None,
        greater_than: Expression | None = None,
        less_than: Expression | None = None,
    ):
        """Initialize a Consistency validator.

        Args:
            field: Field name to validate
            equals: Expected value (as Expression)
            greater_than: Value must be greater than this (as Expression)
            less_than: Value must be less than this (as Expression)
        """
        self.field = field
        self.equals = equals
        self.greater_than = greater_than
        self.less_than = less_than

    def validate(self, instance: Struct) -> None:
        actual = getattr(instance, self.field)

        if self.equals is not None:
            expected = self.equals.evaluate(instance)
            if actual != expected:
                raise InconsistencyError(
                    field=self.field,
                    actual=actual,
                    expected=expected,
                )

        if self.greater_than is not None:
            threshold = self.greater_than.evaluate(instance)
            if not (actual > threshold):
                raise ValidationError(
                    f"Field '{self.field}': {actual} is not > {threshold}"
                )

        if self.less_than is not None:
            threshold = self.less_than.evaluate(instance)
            if not (actual < threshold):
                raise ValidationError(
                    f"Field '{self.field}': {actual} is not < {threshold}"
                )

    def __repr__(self) -> str:
        parts = [f"field={self.field!r}"]
        if self.equals:
            parts.append(f"equals={self.equals!r}")
        if self.greater_than:
            parts.append(f"greater_than={self.greater_than!r}")
        if self.less_than:
            parts.append(f"less_than={self.less_than!r}")
        return f"Consistency({', '.join(parts)})"


class Custom(Validator):
    """Custom validation function.

    Examples:
        >>> class Packet(Struct):
        ...     class Meta:
        ...         validators = [
        ...             Custom(lambda self: self.version in (1, 2, 3),
        ...                    "Unsupported version"),
        ...         ]
    """

    def __init__(
        self,
        func: Callable[[Struct], bool],
        message: str = "Custom validation failed",
    ):
        """Initialize a Custom validator.

        Args:
            func: Validation function that returns True if valid
            message: Error message if validation fails
        """
        self.func = func
        self.message = message

    def validate(self, instance: Struct) -> None:
        if not self.func(instance):
            raise ValidationError(self.message)

    def __repr__(self) -> str:
        return f"Custom({self.message!r})"
