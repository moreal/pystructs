"""Floating-point field types."""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, BinaryIO, Callable, List

from pystructs.base import FixedField
from pystructs.config import Endian
from pystructs.exceptions import UnexpectedEOF

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "Float32",
    "Float64",
)


class Float32(FixedField):
    """32-bit floating point number (IEEE 754 single precision).

    Examples:
        >>> class Point(Struct):
        ...     x = Float32()
        ...     y = Float32()
    """

    size = 4

    def __init__(
        self,
        endian: str | None = None,
        default: float | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a Float32 field.

        Args:
            endian: Byte order ('little' or 'big'), or None to use struct default
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.endian = endian

    def _get_endian(self, instance: Struct) -> str:
        """Get the effective endianness for this field.

        Args:
            instance: The struct instance

        Returns:
            The endianness to use ('little' or 'big')
        """
        if self.endian is not None:
            return self.endian
        return instance._meta.endian

    def parse(self, buffer: BinaryIO, instance: Struct) -> float:
        """Parse a 32-bit float from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed float value

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(4)
        if len(data) < 4:
            raise UnexpectedEOF(expected=4, actual=len(data))

        endian = self._get_endian(instance)
        fmt = "<f" if endian == Endian.LITTLE else ">f"
        return struct.unpack(fmt, data)[0]

    def serialize(self, value: float, instance: Struct) -> bytes:
        """Serialize a 32-bit float to bytes.

        Args:
            value: The float value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        if value is None:
            value = 0.0
        endian = self._get_endian(instance)
        fmt = "<f" if endian == Endian.LITTLE else ">f"
        return struct.pack(fmt, value)


class Float64(FixedField):
    """64-bit floating point number (IEEE 754 double precision).

    Examples:
        >>> class Point3D(Struct):
        ...     x = Float64()
        ...     y = Float64()
        ...     z = Float64()
    """

    size = 8

    def __init__(
        self,
        endian: str | None = None,
        default: float | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a Float64 field.

        Args:
            endian: Byte order ('little' or 'big'), or None to use struct default
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.endian = endian

    def _get_endian(self, instance: Struct) -> str:
        """Get the effective endianness for this field.

        Args:
            instance: The struct instance

        Returns:
            The endianness to use ('little' or 'big')
        """
        if self.endian is not None:
            return self.endian
        return instance._meta.endian

    def parse(self, buffer: BinaryIO, instance: Struct) -> float:
        """Parse a 64-bit float from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed float value

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(8)
        if len(data) < 8:
            raise UnexpectedEOF(expected=8, actual=len(data))

        endian = self._get_endian(instance)
        fmt = "<d" if endian == Endian.LITTLE else ">d"
        return struct.unpack(fmt, data)[0]

    def serialize(self, value: float, instance: Struct) -> bytes:
        """Serialize a 64-bit float to bytes.

        Args:
            value: The float value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        if value is None:
            value = 0.0
        endian = self._get_endian(instance)
        fmt = "<d" if endian == Endian.LITTLE else ">d"
        return struct.pack(fmt, value)
