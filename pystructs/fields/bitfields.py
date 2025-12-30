"""Bit-level field types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Dict, List, Type, TypeVar

from pystructs.base import FixedField
from pystructs.exceptions import UnexpectedEOF

if TYPE_CHECKING:
    pass

__all__ = (
    "BitField",
    "Bit",
    "Bits",
    "BitStructMeta",
    "BitStruct",
)

T = TypeVar("T", bound="BitStruct")


class BitField(ABC):
    """Abstract base class for bit-level fields.

    BitFields are only valid within a BitStruct.
    """

    def __init__(self, default: Any = None):
        """Initialize a bit field.

        Args:
            default: Default value
        """
        self.name: str = ""
        self.default = default
        self._order: int = 0  # For field ordering

    @property
    @abstractmethod
    def bits(self) -> int:
        """Number of bits this field occupies."""
        pass

    @abstractmethod
    def extract(self, value: int, offset: int) -> Any:
        """Extract the field value from an integer.

        Args:
            value: The integer value containing all bits
            offset: Bit offset within the integer

        Returns:
            Extracted field value
        """
        pass

    @abstractmethod
    def insert(self, current: int, value: Any, offset: int) -> int:
        """Insert a field value into an integer.

        Args:
            current: The current integer value
            value: The field value to insert
            offset: Bit offset within the integer

        Returns:
            Updated integer with the field value inserted
        """
        pass

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when the field is assigned to a class attribute."""
        self.name = name


class Bit(BitField):
    """Single bit field (boolean).

    Examples:
        >>> class StatusBits(BitStruct):
        ...     class Meta:
        ...         size = 1
        ...     enabled = Bit()
        ...     ready = Bit()
        ...     error = Bit()
    """

    @property
    def bits(self) -> int:
        return 1

    def extract(self, value: int, offset: int) -> bool:
        """Extract a single bit as boolean.

        Args:
            value: The integer value containing all bits
            offset: Bit offset within the integer

        Returns:
            True if bit is set, False otherwise
        """
        return bool((value >> offset) & 1)

    def insert(self, current: int, value: Any, offset: int) -> int:
        """Insert a boolean as a single bit.

        Args:
            current: The current integer value
            value: Boolean value to insert
            offset: Bit offset within the integer

        Returns:
            Updated integer with the bit set or cleared
        """
        if value:
            return current | (1 << offset)
        else:
            return current & ~(1 << offset)


class Bits(BitField):
    """Multi-bit field (unsigned integer).

    Examples:
        >>> class PackedData(BitStruct):
        ...     class Meta:
        ...         size = 1
        ...     type_id = Bits(3)   # 3 bits for type (0-7)
        ...     value = Bits(5)     # 5 bits for value (0-31)
    """

    def __init__(self, num_bits: int, default: int = 0):
        """Initialize a multi-bit field.

        Args:
            num_bits: Number of bits for this field
            default: Default value
        """
        super().__init__(default=default)
        self._bits = num_bits
        self._mask = (1 << num_bits) - 1

    @property
    def bits(self) -> int:
        return self._bits

    def extract(self, value: int, offset: int) -> int:
        """Extract multiple bits as unsigned integer.

        Args:
            value: The integer value containing all bits
            offset: Bit offset within the integer

        Returns:
            Extracted unsigned integer value
        """
        return (value >> offset) & self._mask

    def insert(self, current: int, value: Any, offset: int) -> int:
        """Insert an unsigned integer into multiple bits.

        Args:
            current: The current integer value
            value: Integer value to insert (will be masked)
            offset: Bit offset within the integer

        Returns:
            Updated integer with the value inserted
        """
        if value is None:
            value = 0
        # Clear the bits at offset
        cleared = current & ~(self._mask << offset)
        # Insert the new value
        return cleared | ((value & self._mask) << offset)


class BitStructMeta(type):
    """Metaclass for BitStruct classes.

    Responsible for:
    - Collecting bit field definitions from class attributes
    - Preserving field declaration order
    - Processing the inner Meta class
    - Validating that total bits match Meta.size
    """

    _field_counter: int = 0

    def __new__(
        mcs, name: str, bases: tuple, namespace: dict, **kwargs: Any
    ) -> BitStructMeta:
        # Skip processing for the base BitStruct class
        if name == "BitStruct" and not bases:
            return super().__new__(mcs, name, bases, namespace)

        # Collect fields from parent classes
        fields: OrderedDict[str, BitField] = OrderedDict()
        for base in bases:
            if hasattr(base, "_bit_fields"):
                fields.update(base._bit_fields)

        # Collect fields from current class
        current_fields: Dict[str, BitField] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, BitField):
                current_fields[key] = value
                value._order = BitStructMeta._field_counter
                BitStructMeta._field_counter += 1

        # Sort by declaration order and merge
        sorted_fields = sorted(current_fields.items(), key=lambda x: x[1]._order)
        for key, field_obj in sorted_fields:
            fields[key] = field_obj

        namespace["_bit_fields"] = fields

        # Process Meta class
        meta = namespace.get("Meta", None)
        if meta:
            size = getattr(meta, "size", None)
            bit_order = getattr(meta, "bit_order", "lsb")  # lsb or msb
        else:
            size = None
            bit_order = "lsb"

        namespace["_size"] = size
        namespace["_bit_order"] = bit_order

        # Create class
        cls = super().__new__(mcs, name, bases, namespace)

        # Call __set_name__ on each field
        for field_name, field_obj in fields.items():
            field_obj.__set_name__(cls, field_name)

        # Validate total bits if size is specified
        if size is not None:
            total_bits = sum(f.bits for f in fields.values())
            expected_bits = size * 8
            if total_bits != expected_bits:
                raise ValueError(
                    f"BitStruct '{name}' has {total_bits} bits but Meta.size={size} "
                    f"expects {expected_bits} bits"
                )

        return cls


class BitStruct(metaclass=BitStructMeta):
    """Base class for bit-level structures.

    BitStruct allows defining fields at the bit level within a fixed-size
    byte container. Fields are packed in declaration order.

    Example:
        >>> class StatusByte(BitStruct):
        ...     class Meta:
        ...         size = 1  # 1 byte = 8 bits
        ...     enabled = Bit()
        ...     mode = Bits(3)
        ...     reserved = Bits(4)
        ...
        >>> status = StatusByte.parse(b'\\x15')
        >>> status.enabled
        True
        >>> status.mode
        2
    """

    _bit_fields: OrderedDict[str, BitField]
    _size: int
    _bit_order: str

    def __init__(self, **kwargs: Any):
        """Initialize a BitStruct instance.

        Args:
            **kwargs: Field values to initialize
        """
        self._data: Dict[str, Any] = {}

        # Initialize fields
        for name, field in self._bit_fields.items():
            if name in kwargs:
                self._data[name] = kwargs[name]
            elif field.default is not None:
                self._data[name] = field.default
            else:
                # Default: False for Bit, 0 for Bits
                if isinstance(field, Bit):
                    self._data[name] = False
                else:
                    self._data[name] = 0

    @classmethod
    def parse(cls: Type[T], data: bytes) -> T:
        """Parse binary data into a BitStruct instance.

        Args:
            data: Binary data to parse

        Returns:
            Parsed BitStruct instance

        Raises:
            UnexpectedEOF: If not enough bytes available
        """
        if cls._size is None:
            raise ValueError(f"BitStruct '{cls.__name__}' has no Meta.size defined")

        if len(data) < cls._size:
            raise UnexpectedEOF(expected=cls._size, actual=len(data))

        # Read the bytes as an integer
        raw_bytes = data[: cls._size]
        value = int.from_bytes(raw_bytes, byteorder="little")

        # Extract fields
        instance = cls.__new__(cls)
        instance._data = {}

        offset = 0
        if cls._bit_order == "msb":
            # MSB first: start from the highest bit
            offset = cls._size * 8
            for name, field in cls._bit_fields.items():
                offset -= field.bits
                instance._data[name] = field.extract(value, offset)
        else:
            # LSB first: start from bit 0
            for name, field in cls._bit_fields.items():
                instance._data[name] = field.extract(value, offset)
                offset += field.bits

        return instance

    def to_bytes(self) -> bytes:
        """Serialize the BitStruct to bytes.

        Returns:
            Serialized bytes
        """
        if self._size is None:
            raise ValueError(f"BitStruct '{self.__class__.__name__}' has no Meta.size")

        value = 0
        offset = 0

        if self._bit_order == "msb":
            # MSB first: start from the highest bit
            offset = self._size * 8
            for name, field in self._bit_fields.items():
                offset -= field.bits
                field_value = self._data.get(name, field.default)
                value = field.insert(value, field_value, offset)
        else:
            # LSB first: start from bit 0
            for name, field in self._bit_fields.items():
                field_value = self._data.get(name, field.default)
                value = field.insert(value, field_value, offset)
                offset += field.bits

        return value.to_bytes(self._size, byteorder="little")

    def __getattribute__(self, name: str) -> Any:
        """Get field value by attribute access."""
        if name.startswith("_") or name in (
            "to_bytes",
            "to_dict",
            "parse",
        ):
            return super().__getattribute__(name)

        bit_fields = super().__getattribute__("_bit_fields")
        if name in bit_fields:
            data = super().__getattribute__("_data")
            return data.get(name)

        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set field value by attribute access."""
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif (
            hasattr(self.__class__, "_bit_fields")
            and name in self.__class__._bit_fields
        ):
            self._data[name] = value
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        fields_str = ", ".join(
            f"{name}={getattr(self, name)!r}" for name in self._bit_fields
        )
        return f"{self.__class__.__name__}({fields_str})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._data == other._data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary.

        Returns:
            Dictionary with field names as keys
        """
        return dict(self._data)


class EmbeddedBitStruct(FixedField):
    """Embedded BitStruct field for use in regular Struct.

    Examples:
        >>> class StatusByte(BitStruct):
        ...     class Meta:
        ...         size = 1
        ...     enabled = Bit()
        ...     mode = Bits(7)
        ...
        >>> class Packet(Struct):
        ...     status = EmbeddedBitStruct(StatusByte)
        ...     data = UInt16()
    """

    def __init__(
        self,
        bitstruct_class: Type[BitStruct],
        default: BitStruct | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize an embedded BitStruct field.

        Args:
            bitstruct_class: The BitStruct class to embed
            default: Default value
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        if bitstruct_class._size is None:
            raise ValueError(
                f"BitStruct '{bitstruct_class.__name__}' has no Meta.size defined"
            )
        super().__init__(default=default, required=required, validators=validators)
        self.bitstruct_class = bitstruct_class
        self.size = bitstruct_class._size

    def parse(self, buffer: BinaryIO, instance: Any) -> BitStruct:
        """Parse BitStruct from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The parent struct instance

        Returns:
            Parsed BitStruct instance
        """
        data = buffer.read(self.size)
        if len(data) < self.size:
            raise UnexpectedEOF(expected=self.size, actual=len(data))
        return self.bitstruct_class.parse(data)

    def serialize(self, value: BitStruct, instance: Any) -> bytes:
        """Serialize BitStruct to bytes.

        Args:
            value: The BitStruct to serialize
            instance: The parent struct instance

        Returns:
            Serialized bytes
        """
        if value is None:
            return bytes(self.size)
        return value.to_bytes()
