from typing import Dict, AnyStr

from pystructs.fields.field import Field


class StructMetaclass(type):
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


class Struct(Field, metaclass=StructMetaclass):
    fields: Dict[AnyStr, Field]

    @property
    def bytes(self):
        return self._bytes

    def __init__(self, _bytes: bytes = b''):
        self._bytes = _bytes

    def __get__(self, instance, owner):
        self._bytes = instance.bytes[self.offset:self.offset+self.size]
        return self
