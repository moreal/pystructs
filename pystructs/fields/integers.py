"""Integer field types."""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, BinaryIO, Callable, List

from pystructs.base import FixedField
from pystructs.config import get_config
from pystructs.exceptions import UnexpectedEOF

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "IntField",
    "Int8",
    "UInt8",
    "Int16",
    "UInt16",
    "Int32",
    "UInt32",
    "Int64",
    "UInt64",
)


class IntField(FixedField):
    """Base class for integer fields.

    Supports configurable byte order (endianness) at field or struct level.
    """

    # Subclasses set these
    size: int = 0
    signed: bool = True
    _format_char: str = ""

    def __init__(
        self,
        default: int = 0,
        endian: str | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize an integer field.

        Args:
            default: Default value (default: 0)
            endian: Byte order ('little', 'big', or None for struct default)
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.endian = endian

    def _get_endian(self, instance: Struct | None) -> str:
        """Get the effective endianness for this field.

        Priority:
        1. Field-level endian
        2. Struct-level endian (from Meta)
        3. Global default endian
        """
        if self.endian:
            return self.endian
        if instance is not None and hasattr(instance, "_meta") and instance._meta:
            return instance._meta.endian
        return get_config().default_endian

    def _get_format(self, instance: Struct | None) -> str:
        """Get the struct format string for this field."""
        endian = self._get_endian(instance)
        prefix = "<" if endian == "little" else ">"
        return prefix + self._format_char

    def parse(self, buffer: BinaryIO, instance: Struct) -> int:
        """Parse an integer from the buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed integer value

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(self.size)
        if len(data) < self.size:
            raise UnexpectedEOF(expected=self.size, got=len(data), field=self.name)
        fmt = self._get_format(instance)
        return struct.unpack(fmt, data)[0]

    def serialize(self, value: int, instance: Struct) -> bytes:
        """Serialize an integer to bytes.

        Args:
            value: Integer value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        fmt = self._get_format(instance)
        return struct.pack(fmt, value)


# Signed integer types


class Int8(IntField):
    """8-bit signed integer (-128 to 127)."""

    size = 1
    signed = True
    _format_char = "b"


class Int16(IntField):
    """16-bit signed integer (-32768 to 32767)."""

    size = 2
    signed = True
    _format_char = "h"


class Int32(IntField):
    """32-bit signed integer."""

    size = 4
    signed = True
    _format_char = "i"


class Int64(IntField):
    """64-bit signed integer."""

    size = 8
    signed = True
    _format_char = "q"


# Unsigned integer types


class UInt8(IntField):
    """8-bit unsigned integer (0 to 255)."""

    size = 1
    signed = False
    _format_char = "B"


class UInt16(IntField):
    """16-bit unsigned integer (0 to 65535)."""

    size = 2
    signed = False
    _format_char = "H"


class UInt32(IntField):
    """32-bit unsigned integer."""

    size = 4
    signed = False
    _format_char = "I"


class UInt64(IntField):
    """64-bit unsigned integer."""

    size = 8
    signed = False
    _format_char = "Q"
