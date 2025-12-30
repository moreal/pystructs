"""Synchronization system for automatic field updates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List

if TYPE_CHECKING:
    from pystructs.struct import Struct

__all__ = ("SyncRule",)


class SyncRule:
    """Rule for synchronizing field values.

    SyncRule defines how one field's value should be computed from other fields.
    Rules are executed when sync() is called on a struct.

    Examples:
        >>> class Packet(Struct):
        ...     class Meta:
        ...         sync_rules = [
        ...             # Update payload_size from payload length
        ...             SyncRule('payload_size', from_field='payload', compute=len),
        ...             # Update checksum from payload
        ...             SyncRule('checksum', compute=lambda self: crc32(self.payload)),
        ...         ]
        ...     payload_size = UInt16()
        ...     payload = Bytes(size=Ref('payload_size'))
        ...     checksum = UInt32()
    """

    def __init__(
        self,
        target: str,
        from_field: str | None = None,
        from_fields: List[str] | None = None,
        compute: Callable | None = None,
    ):
        """Initialize a sync rule.

        Args:
            target: Field name to update (supports dot notation for nested fields)
            from_field: Single source field name (value passed to compute)
            from_fields: Multiple source field names (values passed to compute)
            compute: Function to compute the new value
                     - If from_field: compute(value) -> result
                     - If from_fields: compute(*values) -> result
                     - If neither: compute(instance) -> result
        """
        self.target = target

        if from_field:
            self.sources = [from_field]
        elif from_fields:
            self.sources = from_fields
        else:
            self.sources = []

        self.compute = compute

    def apply(self, instance: Struct) -> None:
        """Apply this rule to update the target field.

        Args:
            instance: The struct instance to update
        """
        if self.sources:
            values = [self._get_nested(instance, name) for name in self.sources]
            if len(values) == 1:
                result = self.compute(values[0])
            else:
                result = self.compute(*values)
        else:
            result = self.compute(instance)

        self._set_nested(instance, self.target, result)

    def _get_nested(self, instance: Struct, path: str) -> Any:
        """Get value from a nested path.

        Args:
            instance: The struct instance
            path: Dot-separated path (e.g., 'header.size')

        Returns:
            The value at the path
        """
        parts = path.split(".")
        obj = instance
        for part in parts:
            obj = getattr(obj, part)
        return obj

    def _set_nested(self, instance: Struct, path: str, value: Any) -> None:
        """Set value at a nested path.

        Args:
            instance: The struct instance
            path: Dot-separated path (e.g., 'header.size')
            value: The value to set
        """
        parts = path.split(".")
        obj = instance
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def __repr__(self) -> str:
        if self.sources:
            return f"SyncRule({self.target!r}, from={self.sources!r})"
        return f"SyncRule({self.target!r})"
