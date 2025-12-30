"""Struct class and metaclass."""

from __future__ import annotations

import warnings
from collections import OrderedDict
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, BinaryIO, Dict, List, Optional, Type, TypeVar

from pystructs.base import BaseField
from pystructs.config import Endian
from pystructs.exceptions import (
    FieldValidationError,
    SerializationError,
    TrailingDataError,
    ValidationErrors,
)

__all__ = (
    "StructMeta",
    "StructOptions",
    "Struct",
)

T = TypeVar("T", bound="Struct")


@dataclass
class StructOptions:
    """Configuration options for a Struct class.

    These are set via the inner Meta class.
    """

    endian: str = field(default=Endian.LITTLE)
    trailing_data: str = field(default="error")  # 'error', 'warn', 'ignore'
    sync_rules: List[Any] = field(default_factory=list)
    validators: List[Any] = field(default_factory=list)

    def inherit_from(self, parent: StructOptions) -> None:
        """Inherit options from a parent Struct.

        Args:
            parent: Parent struct's options
        """
        self.endian = parent.endian
        self.trailing_data = parent.trailing_data
        self.sync_rules = parent.sync_rules.copy()
        self.validators = parent.validators.copy()


class StructMeta(type):
    """Metaclass for Struct classes.

    Responsible for:
    - Collecting field definitions from class attributes
    - Preserving field declaration order
    - Processing the inner Meta class
    - Validating field types
    """

    _field_counter: int = 0

    def __new__(
        mcs, name: str, bases: tuple, namespace: dict, **kwargs: Any
    ) -> StructMeta:
        # Skip processing for the base Struct class
        if name == "Struct" and not bases:
            return super().__new__(mcs, name, bases, namespace)

        # Collect fields from parent classes
        fields: OrderedDict[str, BaseField] = OrderedDict()
        for base in bases:
            if hasattr(base, "_fields"):
                fields.update(base._fields)

        # Collect fields from current class
        current_fields: Dict[str, BaseField] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, BaseField):
                current_fields[key] = value
                value._order = StructMeta._field_counter
                StructMeta._field_counter += 1

        # Sort by declaration order and merge
        sorted_fields = sorted(current_fields.items(), key=lambda x: x[1]._order)
        for key, field_obj in sorted_fields:
            fields[key] = field_obj

        namespace["_fields"] = fields

        # Process Meta class
        meta = namespace.get("Meta", None)
        namespace["_meta"] = mcs._process_meta(meta, bases)

        # Create class
        cls = super().__new__(mcs, name, bases, namespace)

        # Call __set_name__ on each field
        for field_name, field_obj in fields.items():
            field_obj.__set_name__(cls, field_name)

        return cls

    @staticmethod
    def _process_meta(meta: type | None, bases: tuple) -> StructOptions:
        """Process the inner Meta class into StructOptions.

        Args:
            meta: The Meta class (or None)
            bases: Base classes to inherit from

        Returns:
            StructOptions instance
        """
        options = StructOptions()

        # Inherit from parent Meta
        for base in bases:
            if hasattr(base, "_meta") and base._meta is not None:
                options.inherit_from(base._meta)

        # Apply current Meta
        if meta:
            if hasattr(meta, "endian"):
                options.endian = meta.endian
            if hasattr(meta, "trailing_data"):
                options.trailing_data = meta.trailing_data
            if hasattr(meta, "sync_rules"):
                options.sync_rules.extend(meta.sync_rules)
            if hasattr(meta, "validators"):
                options.validators.extend(meta.validators)

        return options


class Struct(metaclass=StructMeta):
    """Base class for binary structures.

    Define fields as class attributes and use parse() to create instances
    from binary data, or to_bytes() to serialize instances.

    Example:
        >>> class Packet(Struct):
        ...     class Meta:
        ...         endian = 'big'
        ...     magic = UInt32(default=0xDEADBEEF)
        ...     version = UInt8(default=1)
        ...     length = UInt16()
        ...
        >>> packet = Packet.parse(raw_bytes)
        >>> packet.version
        1
        >>> packet.to_bytes()
        b'...'
    """

    _fields: OrderedDict[str, BaseField]
    _meta: StructOptions

    def __init__(self, _raw: bytes | None = None, **kwargs: Any):
        """Initialize a struct instance.

        Args:
            _raw: Original raw bytes (internal use for parsing)
            **kwargs: Field values to initialize
        """
        self._data: Dict[str, Any] = {}
        self._raw = _raw
        self._parent: Optional[Struct] = None
        self._root: Struct = self

        # Initialize fields
        for name, field_obj in self._fields.items():
            if name in kwargs:
                self._data[name] = kwargs[name]
            elif field_obj.default is not None:
                if callable(field_obj.default):
                    self._data[name] = field_obj.default()
                else:
                    self._data[name] = field_obj.default
            elif not field_obj.required:
                self._data[name] = None
            # If required and no default, value must be provided before to_bytes()

    # === Class methods ===

    @classmethod
    def parse(
        cls: Type[T],
        data: bytes,
        allow_trailing: bool = False,
    ) -> T:
        """Parse binary data into a struct instance.

        Args:
            data: Binary data to parse
            allow_trailing: If True, ignore trailing bytes after parsing

        Returns:
            Parsed struct instance

        Raises:
            ParseError: If parsing fails
            TrailingDataError: If trailing data exists and not allowed
        """
        stream = BytesIO(data)
        instance = cls._parse_stream(stream)
        instance._raw = data

        # Handle trailing data
        remaining = stream.read()
        if remaining and not allow_trailing:
            policy = cls._meta.trailing_data
            if policy == "error":
                raise TrailingDataError(len(remaining))
            elif policy == "warn":
                warnings.warn(f"Ignoring {len(remaining)} trailing bytes")

        return instance

    @classmethod
    def _parse_stream(
        cls: Type[T],
        stream: BinaryIO,
        parent: Struct | None = None,
    ) -> T:
        """Parse from a stream (internal use).

        Args:
            stream: Binary stream to read from
            parent: Parent struct for nested structs

        Returns:
            Parsed struct instance
        """
        instance = cls.__new__(cls)
        instance._data = {}
        instance._raw = None
        instance._parent = parent
        instance._root = parent._root if parent else instance

        for name, field_obj in cls._fields.items():
            value = field_obj.parse(stream, instance)
            instance._data[name] = value

        return instance

    @classmethod
    def get_fixed_size(cls) -> Optional[int]:
        """Get the fixed size of this struct if all fields are fixed-size.

        Returns:
            Total size in bytes, or None if size is variable
        """
        from pystructs.base import FixedField

        total = 0
        for field_obj in cls._fields.values():
            if isinstance(field_obj, FixedField):
                total += field_obj.size
            else:
                return None
        return total

    # === Instance methods ===

    def to_bytes(
        self,
        sync: bool = False,
        validate: bool = False,
    ) -> bytes:
        """Serialize the struct to bytes.

        Args:
            sync: If True, run sync() before serializing
            validate: If True, run validate() before serializing

        Returns:
            Serialized bytes

        Raises:
            SerializationError: If serialization fails
            ValidationError: If validation fails (when validate=True)
        """
        if sync:
            self.sync()

        if validate:
            self.validate()

        buffer = BytesIO()
        for name, field_obj in self._fields.items():
            value = self._data.get(name)

            if value is None and field_obj.required:
                raise SerializationError(field=name, reason="Missing required field")

            data = field_obj.serialize(value, self)
            buffer.write(data)

        return buffer.getvalue()

    def sync(self, fields: List[str] | None = None) -> Struct:
        """Run synchronization rules to update field values.

        Args:
            fields: Specific fields to sync (default: all)

        Returns:
            self (for method chaining)
        """
        for rule in self._meta.sync_rules:
            if fields is None or rule.target in fields:
                rule.apply(self)
        return self

    def validate(self) -> Struct:
        """Run all validation rules.

        Returns:
            self (for method chaining)

        Raises:
            ValidationErrors: If any validation fails
        """
        errors = []

        # Field-level validation
        for name, field_obj in self._fields.items():
            value = self._data.get(name)
            for validator in field_obj.validators:
                try:
                    validator(value, self)
                except Exception as e:
                    errors.append(FieldValidationError(name, e))

        # Struct-level validation
        for validator in self._meta.validators:
            try:
                validator.validate(self)
            except Exception as e:
                errors.append(e)

        if errors:
            raise ValidationErrors(errors)

        return self

    def get_size(self) -> int:
        """Calculate the current serialization size.

        Returns:
            Size in bytes
        """
        total = 0
        for name, field_obj in self._fields.items():
            total += field_obj.get_size(self)
        return total

    # === Attribute access ===

    def __getattr__(self, name: str) -> Any:
        """Get field value by attribute access.

        Args:
            name: Attribute name

        Returns:
            Field value

        Raises:
            AttributeError: If not a valid field
        """
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self.__class__._fields:
            return self._data.get(name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set field value by attribute access.

        Args:
            name: Attribute name
            value: Value to set
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif name in self.__class__._fields:
            self._data[name] = value
        else:
            super().__setattr__(name, value)

    # === Utilities ===

    def __repr__(self) -> str:
        fields_str = ", ".join(
            f"{name}={getattr(self, name)!r}" for name in self._fields
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
        result = {}
        for name in self._fields:
            value = self._data.get(name)
            if isinstance(value, Struct):
                value = value.to_dict()
            elif isinstance(value, list):
                value = [v.to_dict() if isinstance(v, Struct) else v for v in value]
            result[name] = value
        return result
