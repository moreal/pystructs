from __future__ import annotations

from pystructs.fields.field import Field


class BytesField(Field):
    __bytes: bytes  # bytes of root field

    @property
    def bytes(self) -> bytes:
        return self.__bytes[self.offset:self.offset+self.size]

    @bytes.setter
    def bytes(self, value: bytes):
        self.__bytes = value

    def initialize(self, root: BytesField):
        self.__bytes = root.bytes

    def fetch(self) -> bytes:
        return self.bytes
