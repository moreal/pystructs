from typing import Dict, AnyStr

from pystructs.fields import IntField, BytesField
from pystructs.fields.field import Field

__all__ = [
    'ConstantStruct',
    'VariableStruct',
]


class ConstantStructMetaclass(type):
    def __new__(mcs, name, bases, attrs: dict):
        offset = 0

        attrs['fields'] = dict()

        for name, field in attrs.items():
            if not isinstance(field, Field):
                continue

            attrs['fields'][name] = field

            field.offset = offset
            offset += field.size

        attrs['size'] = offset

        return super().__new__(mcs, name, bases, attrs)


class VariableStructMetaclass(type):
    def __new__(mcs, name, bases, attrs: dict):
        attrs['fields'] = dict(filter(lambda x: isinstance(x[1], Field), attrs.items()))
        return super().__new__(mcs, name, bases, attrs)


class Struct(BytesField):
    fields: Dict[AnyStr, Field]

    @property
    def bytes(self):
        return self._bytes

    def __init__(self, _bytes: bytes = b''):
        self._bytes = _bytes
        self._initialize()

    def __get__(self, instance, owner):
        self._bytes = instance.bytes[self.offset:self.offset+self.size]
        return self

    def _initialize(self):
        pass


class ConstantStruct(Struct, metaclass=ConstantStructMetaclass):
    pass


class VariableStruct(Struct, metaclass=VariableStructMetaclass):
    def _initialize(self):
        offset = 0

        for field in self.fields.values():
            field.offset = offset
            offset += field.size

        self.size = offset

