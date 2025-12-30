"""pystructs - Django-like declarative binary parsing library."""

from pystructs.base import BaseField, FixedField
from pystructs.config import Endian, configure, get_config
from pystructs.exceptions import (
    FieldValidationError,
    InconsistencyError,
    ParseError,
    PyStructError,
    SerializationError,
    StructDefinitionError,
    TrailingDataError,
    UnexpectedEOF,
    ValidationError,
    ValidationErrors,
)
from pystructs.expressions import BinaryOp, Checksum, Const, Expression, Len, Value
from pystructs.fields import (
    Array,
    Bit,
    BitField,
    Bits,
    BitStruct,
    BitStructMeta,
    Bool,
    Bytes,
    Conditional,
    EmbeddedBitStruct,
    EmbeddedStruct,
    Enum,
    FixedBytes,
    FixedString,
    Flags,
    FlagSet,
    Float32,
    Float64,
    Int8,
    Int16,
    Int32,
    Int64,
    IntField,
    NullTerminatedString,
    Padding,
    String,
    Switch,
    UInt8,
    UInt16,
    UInt32,
    UInt64,
)
from pystructs.ref import Ref, RefComparison, RefLogical
from pystructs.struct import Struct, StructMeta, StructOptions
from pystructs.sync import SyncRule
from pystructs.validate import (
    BytePattern,
    Consistency,
    Custom,
    FieldValidator,
    OneOf,
    Range,
    Regex,
    Validator,
)

__version__ = "0.4.0"

__all__ = (
    # Version
    "__version__",
    # Base classes
    "BaseField",
    "FixedField",
    # Struct
    "Struct",
    "StructMeta",
    "StructOptions",
    # Reference
    "Ref",
    "RefComparison",
    "RefLogical",
    # Configuration
    "Endian",
    "configure",
    "get_config",
    # Exceptions
    "PyStructError",
    "ParseError",
    "UnexpectedEOF",
    "TrailingDataError",
    "ValidationError",
    "FieldValidationError",
    "InconsistencyError",
    "ValidationErrors",
    "SerializationError",
    "StructDefinitionError",
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
    # Sync
    "SyncRule",
    # Expressions
    "Expression",
    "Len",
    "Value",
    "Const",
    "Checksum",
    "BinaryOp",
    # Validators
    "Validator",
    "FieldValidator",
    "Range",
    "OneOf",
    "Regex",
    "BytePattern",
    "Consistency",
    "Custom",
)
