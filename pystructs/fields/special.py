"""Special field types."""

from __future__ import annotations

import enum as _enum
from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Dict, List, Set, Type

from pystructs.base import BaseField, FixedField
from pystructs.exceptions import UnexpectedEOF
from pystructs.ref import Ref

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "Bool",
    "Padding",
    "Flags",
    "FlagSet",
    "Enum",
)


class Bool(FixedField):
    """Boolean field (1 byte).

    Reads/writes a single byte where 0 is False and non-zero is True.

    Examples:
        >>> class Message(Struct):
        ...     is_active = Bool()
        ...     has_payload = Bool(default=False)
    """

    size = 1

    def __init__(
        self,
        default: bool | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a Bool field.

        Args:
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)

    def parse(self, buffer: BinaryIO, instance: Struct) -> bool:
        """Parse a boolean from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed boolean value

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(1)
        if len(data) < 1:
            raise UnexpectedEOF(expected=1, actual=0)
        return data[0] != 0

    def serialize(self, value: bool, instance: Struct) -> bytes:
        """Serialize a boolean to bytes.

        Args:
            value: The boolean value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes (0x00 or 0x01)
        """
        if value is None:
            value = False
        return bytes([1 if value else 0])


class Padding(BaseField):
    """Padding bytes that are ignored during parsing.

    Padding is used to align fields or skip reserved bytes.
    The padding bytes are not stored in the struct.

    Examples:
        >>> class AlignedData(Struct):
        ...     value = UInt8()
        ...     _pad = Padding(size=3)  # Align to 4 bytes
        ...     data = UInt32()
    """

    def __init__(
        self,
        size: int | Ref,
        fill: int = 0x00,
    ):
        """Initialize a Padding field.

        Args:
            size: Number of padding bytes (integer or Ref)
            fill: Byte value to use when serializing (default 0x00)
        """
        super().__init__(default=None, required=False, validators=None)
        self.size_spec = size
        self.fill = fill

    def _get_size_value(self, instance: Struct) -> int:
        """Get the current padding size.

        Args:
            instance: The struct instance

        Returns:
            Number of padding bytes
        """
        if isinstance(self.size_spec, Ref):
            return self.size_spec.resolve(instance)
        return self.size_spec

    def get_size(self, instance: Struct) -> int:
        """Get the size of the padding.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        return self._get_size_value(instance)

    def parse(self, buffer: BinaryIO, instance: Struct) -> None:
        """Parse (skip) padding bytes from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            None (padding is not stored)

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        size = self._get_size_value(instance)
        data = buffer.read(size)
        if len(data) < size:
            raise UnexpectedEOF(expected=size, actual=len(data))
        return None

    def serialize(self, value: Any, instance: Struct) -> bytes:
        """Serialize padding bytes.

        Args:
            value: Ignored (padding has no value)
            instance: The struct instance being serialized

        Returns:
            Padding bytes filled with the fill value
        """
        size = self._get_size_value(instance)
        return bytes([self.fill] * size)


class FlagSet(set):
    """A set of active flags from a Flags field.

    This is a regular Python set with additional properties for
    accessing the raw integer value.

    Examples:
        >>> flags = packet.flags  # Returns FlagSet
        >>> 'READ' in flags
        True
        >>> flags.value
        5
    """

    def __init__(self, flags: Set[str], value: int, all_flags: Dict[str, int]):
        """Initialize a FlagSet.

        Args:
            flags: Set of active flag names
            value: The raw integer value
            all_flags: Mapping of flag names to bit values
        """
        super().__init__(flags)
        self._value = value
        self._all_flags = all_flags

    @property
    def value(self) -> int:
        """Get the raw integer value."""
        return self._value

    def __repr__(self) -> str:
        flags_str = ", ".join(sorted(self))
        return f"FlagSet({{{flags_str}}}, value={self._value})"


class Flags(BaseField):
    """Bit flags field.

    Maps individual bits to named flags, returning a FlagSet.

    Examples:
        >>> class Permission(Struct):
        ...     flags = Flags(
        ...         size=1,
        ...         flags={
        ...             'READ': 0x01,
        ...             'WRITE': 0x02,
        ...             'EXECUTE': 0x04,
        ...         }
        ...     )
        ...
        >>> p = Permission.parse(b'\\x05')
        >>> 'READ' in p.flags
        True
        >>> 'EXECUTE' in p.flags
        True
        >>> 'WRITE' in p.flags
        False
    """

    def __init__(
        self,
        size: int,
        flags: Dict[str, int],
        default: Set[str] | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a Flags field.

        Args:
            size: Size in bytes (1, 2, 4, or 8)
            flags: Mapping of flag names to bit values
            default: Default set of flag names
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.size = size
        self.flags = flags
        self._reverse_flags = {v: k for k, v in flags.items()}

    def get_size(self, instance: Struct) -> int:
        """Get the size of the flags field.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        return self.size

    def parse(self, buffer: BinaryIO, instance: Struct) -> FlagSet:
        """Parse flags from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            FlagSet with active flag names

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        data = buffer.read(self.size)
        if len(data) < self.size:
            raise UnexpectedEOF(expected=self.size, actual=len(data))

        value = int.from_bytes(data, byteorder="little")

        active_flags = set()
        for name, bit_value in self.flags.items():
            if value & bit_value:
                active_flags.add(name)

        return FlagSet(active_flags, value, self.flags)

    def serialize(self, value: FlagSet | Set[str] | int, instance: Struct) -> bytes:
        """Serialize flags to bytes.

        Args:
            value: FlagSet, set of flag names, or raw integer
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        if value is None:
            value = 0
        elif isinstance(value, FlagSet):
            value = value.value
        elif isinstance(value, set):
            int_value = 0
            for name in value:
                if name in self.flags:
                    int_value |= self.flags[name]
            value = int_value

        return value.to_bytes(self.size, byteorder="little")


class Enum(BaseField):
    """Enum field that maps integer values to enum members.

    Uses Python's enum module for type-safe enum handling.

    Examples:
        >>> from enum import IntEnum
        >>>
        >>> class MessageType(IntEnum):
        ...     REQUEST = 1
        ...     RESPONSE = 2
        ...     ERROR = 3
        ...
        >>> class Message(Struct):
        ...     msg_type = Enum(MessageType, size=1)
        ...
        >>> m = Message.parse(b'\\x02')
        >>> m.msg_type
        <MessageType.RESPONSE: 2>
        >>> m.msg_type == MessageType.RESPONSE
        True
    """

    def __init__(
        self,
        enum_class: Type[_enum.IntEnum],
        size: int = 1,
        default: _enum.IntEnum | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize an Enum field.

        Args:
            enum_class: The IntEnum class to use
            size: Size in bytes (1, 2, 4, or 8)
            default: Default enum value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.enum_class = enum_class
        self.size = size

    def get_size(self, instance: Struct) -> int:
        """Get the size of the enum field.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        return self.size

    def parse(self, buffer: BinaryIO, instance: Struct) -> _enum.IntEnum:
        """Parse enum from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Enum member

        Raises:
            UnexpectedEOF: If not enough bytes available
            ValueError: If value is not a valid enum member
        """
        data = buffer.read(self.size)
        if len(data) < self.size:
            raise UnexpectedEOF(expected=self.size, actual=len(data))

        value = int.from_bytes(data, byteorder="little")

        try:
            return self.enum_class(value)
        except ValueError:
            # If strict enum matching fails, return the raw int
            # This follows the "dumb by default" principle
            return value

    def serialize(self, value: _enum.IntEnum | int, instance: Struct) -> bytes:
        """Serialize enum to bytes.

        Args:
            value: Enum member or raw integer
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        if value is None:
            value = 0
        elif isinstance(value, _enum.IntEnum):
            value = value.value

        return value.to_bytes(self.size, byteorder="little")
