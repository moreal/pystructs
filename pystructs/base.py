"""Base field classes for pystructs.

This module provides the abstract base classes for all field types:
- BaseField: Abstract base with descriptor protocol
- FixedField: Base for fixed-size fields

All field types must inherit from BaseField and implement the
parse/serialize methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, BinaryIO, List, Optional, Protocol

if TYPE_CHECKING:
    from pystructs.struct import Struct


class FieldValidator(Protocol):
    """Protocol for field-level validators."""

    def __call__(self, value: Any, instance: Struct) -> None:
        """Validate a field value.

        Args:
            value: The field value to validate
            instance: The struct instance

        Raises:
            ValidationError: If validation fails
        """
        ...


__all__ = (
    "BaseField",
    "FixedField",
)


class BaseField(ABC):
    """Abstract base class for all fields.

    All field types must inherit from this class and implement:
    - get_size(instance): Return the byte size of the field
    - parse(buffer, instance): Parse bytes from buffer and return value
    - serialize(value, instance): Convert value to bytes

    Fields also implement the descriptor protocol for attribute access.
    """

    # Set by metaclass to track declaration order
    _order: int = 0

    def __init__(
        self,
        default: Any = None,
        required: bool = True,
        validators: Optional[List[FieldValidator]] = None,
    ):
        """Initialize a field.

        Args:
            default: Default value for this field. Can be a value or callable.
                If callable, it will be called to get the default value.
            required: If True, field must have a value for serialization.
                Missing required fields raise SerializationError.
            validators: List of validator functions for this field.
                Each validator should accept (value, instance) and raise
                ValidationError if validation fails.
        """
        self.name: Optional[str] = None
        self.default = default
        self.required = required
        self.validators: List[FieldValidator] = validators or []

    @abstractmethod
    def get_size(self, instance: Struct) -> int:
        """Get the byte size of this field.

        Args:
            instance: The struct instance (for Ref resolution)

        Returns:
            Size in bytes
        """
        pass

    @abstractmethod
    def parse(self, buffer: BinaryIO, instance: Struct) -> Any:
        """Parse bytes from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed value
        """
        pass

    @abstractmethod
    def serialize(self, value: Any, instance: Struct) -> bytes:
        """Serialize value to bytes.

        Args:
            value: Value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        pass

    def validate(self, value: Any, instance: Struct) -> None:
        """Run field-level validators.

        Args:
            value: Value to validate
            instance: The struct instance

        Raises:
            ValidationError: If validation fails
        """
        for validator in self.validators:
            validator(value, instance)

    # Descriptor protocol

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when field is assigned to a class attribute.

        Args:
            owner: The class that owns this field
            name: The attribute name
        """
        self.name = name

    def __get__(self, instance: Struct | None, owner: type) -> Any:
        """Get the field value from an instance.

        Args:
            instance: The struct instance (or None for class access)
            owner: The class that owns this field

        Returns:
            The field value, or the field itself for class access
        """
        if instance is None:
            return self
        return instance._data.get(self.name)

    def __set__(self, instance: Struct, value: Any) -> None:
        """Set the field value on an instance.

        Args:
            instance: The struct instance
            value: The value to set
        """
        instance._data[self.name] = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class FixedField(BaseField):
    """Base class for fixed-size fields.

    Subclasses should set the `size` class attribute to specify the byte size.
    """

    size: int = 0

    def get_size(self, instance: Struct) -> int:
        """Get the byte size of this field.

        Returns:
            The fixed size in bytes
        """
        return self.size
