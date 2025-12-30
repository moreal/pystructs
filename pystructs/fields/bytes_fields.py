"""Bytes field types."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Callable, List

from pystructs.base import BaseField, FixedField
from pystructs.exceptions import UnexpectedEOF
from pystructs.ref import Ref

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "FixedBytes",
    "Bytes",
)


class FixedBytes(FixedField):
    """Fixed-length bytes field.

    Examples:
        >>> class Header(Struct):
        ...     magic = FixedBytes(4)  # Always 4 bytes
    """

    def __init__(
        self,
        length: int,
        default: bytes | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a fixed-length bytes field.

        Args:
            length: Fixed byte length
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.size = length

    def parse(self, buffer: BinaryIO, instance: Struct) -> bytes:
        """Parse fixed bytes from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed bytes

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(self.size)
        if len(data) < self.size:
            raise UnexpectedEOF(expected=self.size, got=len(data), field=self.name)
        return data

    def serialize(self, value: bytes, instance: Struct) -> bytes:
        """Serialize bytes value.

        Args:
            value: Bytes to serialize
            instance: The struct instance being serialized

        Returns:
            The bytes value (dumb serialization, no size validation)
        """
        return value


class Bytes(BaseField):
    """Variable-length bytes field.

    Size can be specified as a fixed integer or as a Ref to another field.

    Examples:
        >>> class Packet(Struct):
        ...     length = UInt16()
        ...     data = Bytes(size=Ref('length'))  # Size from another field
        ...
        >>> class Fixed(Struct):
        ...     data = Bytes(size=10)  # Fixed size
    """

    def __init__(
        self,
        size: int | Ref,
        default: bytes | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a variable-length bytes field.

        Args:
            size: Size in bytes (integer) or reference to size field (Ref)
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.size_spec = size

    def get_size(self, instance: Struct) -> int:
        """Get the current size of this field.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        if isinstance(self.size_spec, Ref):
            return self.size_spec.resolve(instance)
        return self.size_spec

    def parse(self, buffer: BinaryIO, instance: Struct) -> bytes:
        """Parse variable bytes from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed bytes

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        size = self.get_size(instance)
        data = buffer.read(size)
        if len(data) < size:
            raise UnexpectedEOF(expected=size, got=len(data), field=self.name)
        return data

    def serialize(self, value: bytes, instance: Struct) -> bytes:
        """Serialize bytes value.

        Note: This is "dumb" serialization - no size validation is performed.
        Use sync() and validate() for consistency checks.

        Args:
            value: Bytes to serialize
            instance: The struct instance being serialized

        Returns:
            The bytes value
        """
        return value
