"""Field types for pystructs."""

from pystructs.fields.bitfields import (
    Bit,
    BitField,
    Bits,
    BitStruct,
    BitStructMeta,
    EmbeddedBitStruct,
)
from pystructs.fields.bytes_fields import Bytes, FixedBytes
from pystructs.fields.composite import Array, Conditional, EmbeddedStruct, Switch
from pystructs.fields.floats import Float32, Float64
from pystructs.fields.integers import (
    Int8,
    Int16,
    Int32,
    Int64,
    IntField,
    UInt8,
    UInt16,
    UInt32,
    UInt64,
)
from pystructs.fields.special import Bool, Enum, Flags, FlagSet, Padding
from pystructs.fields.strings import FixedString, NullTerminatedString, String

__all__ = (
    # Integer fields
    "IntField",
    "Int8",
    "UInt8",
    "Int16",
    "UInt16",
    "Int32",
    "UInt32",
    "Int64",
    "UInt64",
    # Float fields
    "Float32",
    "Float64",
    # Bytes fields
    "FixedBytes",
    "Bytes",
    # String fields
    "FixedString",
    "String",
    "NullTerminatedString",
    # Composite fields
    "Array",
    "EmbeddedStruct",
    "Conditional",
    "Switch",
    # Special fields
    "Bool",
    "Padding",
    "Flags",
    "FlagSet",
    "Enum",
    # Bit fields
    "BitField",
    "Bit",
    "Bits",
    "BitStructMeta",
    "BitStruct",
    "EmbeddedBitStruct",
)
