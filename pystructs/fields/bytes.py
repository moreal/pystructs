from __future__ import annotations

from typing import Optional

from pystructs.fields.field import Field


__all__ = [
    "BytesField"
]


class BytesField(Field):
    bytes: Optional[bytes]  # bytes of root field

    def __init__(self, size: int):
        super().__init__(size)
        self.bytes = None

    def initialize(self, root: BytesField):
        self.bytes = root.bytes

    def fetch(self) -> bytes:
        return self.bytes[self.offset:self.offset+self.size]
