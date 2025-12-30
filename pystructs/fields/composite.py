"""Composite field types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Dict, List, Type

from pystructs.base import BaseField
from pystructs.ref import Ref, RefComparison, RefLogical

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = (
    "Array",
    "EmbeddedStruct",
    "Conditional",
    "Switch",
)


class Array(BaseField):
    """Array of repeated fields.

    Count can be specified as a fixed integer or as a Ref to another field.

    Examples:
        >>> class Packet(Struct):
        ...     count = UInt16()
        ...     items = Array(UInt32(), count=Ref('count'))
        ...
        >>> class FixedArray(Struct):
        ...     values = Array(UInt8(), count=10)
    """

    def __init__(
        self,
        item_field: BaseField,
        count: int | Ref,
        default: List | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize an array field.

        Args:
            item_field: The field type for each item
            count: Number of items (integer) or reference to count field (Ref)
            default: Default value (list)
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.item_field = item_field
        self.count_spec = count

    def get_count(self, instance: Struct) -> int:
        """Get the current count of items.

        Args:
            instance: The struct instance

        Returns:
            Number of items
        """
        if isinstance(self.count_spec, Ref):
            return self.count_spec.resolve(instance)
        return self.count_spec

    def get_size(self, instance: Struct) -> int:
        """Get the total size of this array.

        Args:
            instance: The struct instance

        Returns:
            Total size in bytes
        """
        count = self.get_count(instance)
        item_size = self.item_field.get_size(instance)
        return count * item_size

    def parse(self, buffer: BinaryIO, instance: Struct) -> List[Any]:
        """Parse array from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            List of parsed items
        """
        count = self.get_count(instance)
        items = []
        for _ in range(count):
            item = self.item_field.parse(buffer, instance)
            items.append(item)
        return items

    def serialize(self, value: List[Any], instance: Struct) -> bytes:
        """Serialize array to bytes.

        Note: This is "dumb" serialization - no count validation.

        Args:
            value: List of items to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        parts = []
        for item in value:
            parts.append(self.item_field.serialize(item, instance))
        return b"".join(parts)


class EmbeddedStruct(BaseField):
    """Embedded struct field.

    Contains a nested Struct as a field value. The nested struct maintains
    a parent reference for Ref path resolution.

    Examples:
        >>> class Header(Struct):
        ...     magic = UInt32(default=0xDEADBEEF)
        ...     version = UInt8(default=1)
        ...
        >>> class Packet(Struct):
        ...     header = EmbeddedStruct(Header)
        ...     data = Bytes(size=10)
    """

    def __init__(
        self,
        struct_class: Type[Struct],
        default: Struct | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize an embedded struct field.

        Args:
            struct_class: The Struct class to embed
            default: Default value (a Struct instance or None)
            required: If True, field must have a value for serialization
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.struct_class = struct_class

    def get_size(self, instance: Struct) -> int:
        """Get the size of the embedded struct.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        value = instance._data.get(self.name)
        if value is not None:
            return value.get_size()
        # If no value yet, try to get fixed size from class
        fixed_size = self.struct_class.get_fixed_size()
        if fixed_size is not None:
            return fixed_size
        return 0

    def parse(self, buffer: BinaryIO, instance: Struct) -> Struct:
        """Parse embedded struct from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The parent struct instance

        Returns:
            Parsed nested Struct instance
        """
        nested = self.struct_class._parse_stream(buffer, parent=instance)
        return nested

    def serialize(self, value: Struct, instance: Struct) -> bytes:
        """Serialize embedded struct to bytes.

        Args:
            value: The nested Struct to serialize
            instance: The parent struct instance

        Returns:
            Serialized bytes
        """
        if value is None:
            return b""
        return value.to_bytes()


class Conditional(BaseField):
    """Conditional field that only exists when a condition is met.

    The `when` parameter determines if the field exists. It can be:
    - A callable taking the instance and returning bool
    - A RefComparison (e.g., Ref('version') >= 2)
    - A RefLogical (combined comparisons)

    Examples:
        >>> class Packet(Struct):
        ...     version = UInt8()
        ...     # Only present in version 2+
        ...     extra_data = Conditional(UInt32(), when=Ref('version') >= 2)
        ...
        >>> class Message(Struct):
        ...     flags = UInt8()
        ...     # Present when flags bit 0 is set
        ...     optional = Conditional(UInt16(), when=lambda s: s.flags & 1)
    """

    def __init__(
        self,
        field: BaseField,
        when: Callable[[Struct], bool] | RefComparison | RefLogical,
        default: Any = None,
        required: bool = False,  # Default to False for conditional fields
        validators: List[Callable] | None = None,
    ):
        """Initialize a conditional field.

        Args:
            field: The field to conditionally include
            when: Condition for field presence
            default: Default value when field is not present
            required: If True, field must be present when condition is met
            validators: List of validator functions
        """
        super().__init__(default=default, required=required, validators=validators)
        self.field = field
        self.when = when

    def _evaluate_condition(self, instance: Struct) -> bool:
        """Evaluate the condition.

        Args:
            instance: The struct instance

        Returns:
            True if the condition is met
        """
        if callable(self.when):
            return self.when(instance)
        elif isinstance(self.when, (RefComparison, RefLogical)):
            return self.when.evaluate(instance)
        return bool(self.when)

    def get_size(self, instance: Struct) -> int:
        """Get the size of the conditional field.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes (0 if condition not met)
        """
        if self._evaluate_condition(instance):
            return self.field.get_size(instance)
        return 0

    def parse(self, buffer: BinaryIO, instance: Struct) -> Any:
        """Parse conditional field from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed value or None if condition not met
        """
        if self._evaluate_condition(instance):
            return self.field.parse(buffer, instance)
        return self.default

    def serialize(self, value: Any, instance: Struct) -> bytes:
        """Serialize conditional field to bytes.

        Args:
            value: The value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes (empty if condition not met)
        """
        if self._evaluate_condition(instance):
            if value is None:
                value = self.default
            if value is not None:
                return self.field.serialize(value, instance)
        return b""


class Switch(BaseField):
    """Field that can be one of multiple types based on a discriminator.

    Switch selects between different field types based on the value of
    another field. This is useful for tagged unions and variant types.

    Examples:
        >>> class Message(Struct):
        ...     msg_type = UInt8()
        ...     payload = Switch(
        ...         discriminator=Ref('msg_type'),
        ...         cases={
        ...             1: TextPayload,
        ...             2: BinaryPayload,
        ...             3: StatusPayload,
        ...         },
        ...         default=RawPayload,
        ...     )
    """

    def __init__(
        self,
        discriminator: Ref | Callable[[Struct], Any],
        cases: Dict[Any, BaseField | Type[Struct]],
        default: BaseField | Type[Struct] | None = None,
        required: bool = True,
        validators: List[Callable] | None = None,
    ):
        """Initialize a switch field.

        Args:
            discriminator: Ref or callable to get the discriminator value
            cases: Mapping from discriminator values to field types
            default: Default field type when no case matches
            required: If True, a case must match or default must be provided
            validators: List of validator functions
        """
        super().__init__(default=None, required=required, validators=validators)
        self.discriminator = discriminator
        self.cases = self._normalize_cases(cases)
        self.default_field = self._normalize_field(default) if default else None

    def _normalize_cases(
        self, cases: Dict[Any, BaseField | Type[Struct]]
    ) -> Dict[Any, BaseField]:
        """Convert Struct classes to EmbeddedStruct fields.

        Args:
            cases: Original cases dict

        Returns:
            Normalized cases with all BaseField instances
        """

        normalized = {}
        for key, value in cases.items():
            normalized[key] = self._normalize_field(value)
        return normalized

    def _normalize_field(self, field: BaseField | Type[Struct]) -> BaseField:
        """Normalize a field or Struct class to a BaseField.

        Args:
            field: Field or Struct class

        Returns:
            BaseField instance
        """
        from pystructs.struct import Struct as StructClass

        if isinstance(field, type) and issubclass(field, StructClass):
            return EmbeddedStruct(field)
        return field

    def _get_discriminator_value(self, instance: Struct) -> Any:
        """Get the current discriminator value.

        Args:
            instance: The struct instance

        Returns:
            The discriminator value
        """
        if isinstance(self.discriminator, Ref):
            return self.discriminator.resolve(instance)
        elif callable(self.discriminator):
            return self.discriminator(instance)
        return self.discriminator

    def _get_field_for_value(self, value: Any) -> BaseField | None:
        """Get the field type for a discriminator value.

        Args:
            value: The discriminator value

        Returns:
            The corresponding field or None
        """
        if value in self.cases:
            return self.cases[value]
        return self.default_field

    def get_size(self, instance: Struct) -> int:
        """Get the size of the selected field.

        Args:
            instance: The struct instance

        Returns:
            Size in bytes
        """
        disc_value = self._get_discriminator_value(instance)
        field = self._get_field_for_value(disc_value)
        if field is not None:
            return field.get_size(instance)
        return 0

    def parse(self, buffer: BinaryIO, instance: Struct) -> Any:
        """Parse the selected field from buffer.

        Args:
            buffer: Binary stream to read from
            instance: The struct instance being parsed

        Returns:
            Parsed value

        Raises:
            ValueError: If no matching case and no default
        """
        disc_value = self._get_discriminator_value(instance)
        field = self._get_field_for_value(disc_value)
        if field is None:
            if self.required:
                raise ValueError(
                    f"No case for discriminator value {disc_value!r} and no default"
                )
            return None
        return field.parse(buffer, instance)

    def serialize(self, value: Any, instance: Struct) -> bytes:
        """Serialize the selected field to bytes.

        Args:
            value: The value to serialize
            instance: The struct instance being serialized

        Returns:
            Serialized bytes
        """
        disc_value = self._get_discriminator_value(instance)
        field = self._get_field_for_value(disc_value)
        if field is None:
            return b""
        return field.serialize(value, instance)
