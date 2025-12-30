"""String field types."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Callable, List

from pystructs.base import BaseField, FixedField
from pystructs.exceptions import SerializationError, UnexpectedEOF
from pystructs.ref import Ref

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "FixedString",
    "String",
    "NullTerminatedString",
)


class FixedString(FixedField):
    """Fixed-length string field.

    Parses a fixed number of bytes and decodes as string.
    Supports padding for serialization.

    Examples:
        >>> class Record(Struct):
        ...     name = FixedString(20, encoding='utf-8')
    """

    def __init__(
        self,
        length: int,
        encoding: str = "utf-8",
        padding: bytes = b"\x00",
        default: str | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a fixed-length string field.

        Args:
            length: Fixed byte length
            encoding: String encoding (default: utf-8)
            padding: Padding byte for shorter strings (default: null)
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.size = length
        self.encoding = encoding
        self.padding = padding

    def parse(self, buffer: BinaryIO, instance: Struct) -> str:
        """Parse fixed string from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed string with trailing padding removed

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(self.size)
        if len(data) < self.size:
            raise UnexpectedEOF(expected=self.size, got=len(data), field=self.name)
        return data.rstrip(self.padding).decode(self.encoding)

    def serialize(self, value: str, instance: Struct) -> bytes:
        """Serialize string value with padding.

        Args:
            value: String to serialize
            instance: The struct instance being serialized

        Returns:
            Encoded and padded bytes

        Raises:
            SerializationError: If encoded string exceeds field length
        """
        encoded = value.encode(self.encoding)
        if len(encoded) > self.size:
            raise SerializationError(
                field=self.name,
                reason=f"String too long: {len(encoded)} > {self.size}",
            )
        return encoded.ljust(self.size, self.padding)


class String(BaseField):
    """Variable-length string field.

    Length can be specified as a fixed integer or as a Ref to another field.

    Examples:
        >>> class Message(Struct):
        ...     length = UInt8()
        ...     text = String(length=Ref('length'))
    """

    def __init__(
        self,
        length: int | Ref,
        encoding: str = "utf-8",
        default: str | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a variable-length string field.

        Args:
            length: Length in bytes (integer) or reference to length field (Ref)
            encoding: String encoding (default: utf-8)
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.length_spec = length
        self.encoding = encoding

    def get_size(self, instance: Struct) -> int:
        """Get the current size of this field.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        if isinstance(self.length_spec, Ref):
            return self.length_spec.resolve(instance)
        return self.length_spec

    def parse(self, buffer: BinaryIO, instance: Struct) -> str:
        """Parse variable string from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed string

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        length = self.get_size(instance)
        data = buffer.read(length)
        if len(data) < length:
            raise UnexpectedEOF(expected=length, got=len(data), field=self.name)
        return data.decode(self.encoding)

    def serialize(self, value: str, instance: Struct) -> bytes:
        """Serialize string value.

        Note: This is "dumb" serialization - no length validation.

        Args:
            value: String to serialize
            instance: The struct instance being serialized

        Returns:
            Encoded bytes
        """
        return value.encode(self.encoding)


class NullTerminatedString(BaseField):
    """Null-terminated string field.

    Reads bytes until a null byte is encountered.

    Examples:
        >>> class CString(Struct):
        ...     name = NullTerminatedString()
    """

    def __init__(
        self,
        encoding: str = "utf-8",
        include_null: bool = True,
        max_length: int | None = None,
        default: str | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a null-terminated string field.

        Args:
            encoding: String encoding (default: utf-8)
            include_null: If True, include null byte in serialization
            max_length: Maximum length to read (safety limit)
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.encoding = encoding
        self.include_null = include_null
        self.max_length = max_length
        self._parsed_size = 0

    def get_size(self, instance: Struct) -> int:
        """Get the size of this field.

        Returns the size of the last parsed string (including null if applicable).
        For unparsed instances, returns 0.
        """
        return self._parsed_size

    def parse(self, buffer: BinaryIO, instance: Struct) -> str:
        """Parse null-terminated string from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed string (without null terminator)
        """
        result = bytearray()
        bytes_read = 0

        while True:
            byte = buffer.read(1)
            if not byte:
                break  # EOF
            bytes_read += 1
            if byte == b"\x00":
                break
            result.append(byte[0])
            if self.max_length and bytes_read >= self.max_length:
                break

        self._parsed_size = bytes_read
        return result.decode(self.encoding)

    def serialize(self, value: str, instance: Struct) -> bytes:
        """Serialize string with null terminator.

        Args:
            value: String to serialize
            instance: The struct instance being serialized

        Returns:
            Encoded bytes with optional null terminator
        """
        encoded = value.encode(self.encoding)
        if self.include_null:
            return encoded + b"\x00"
        return encoded
