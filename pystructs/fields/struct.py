from copy import deepcopy
from typing import Dict, AnyStr

from pystructs.fields import IntField, BytesField
from pystructs.fields.field import Field
from pystructs.fields.variable import VariableBytesField
from pystructs.interfaces import IConstant, IVariable
from pystructs.utils import deepattr

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

            if isinstance(field, IVariable):
                raise TypeError("ConstantStruct can't have `IVariable` Field")

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
        for _, field in self.fields.items():
            field.parent = self

    def __getitem__(self, item):
        return self.fields[item]


class ConstantStruct(Struct, IConstant, metaclass=ConstantStructMetaclass):
    pass


class VariableStruct(Struct, IVariable, metaclass=VariableStructMetaclass):
    def _initialize(self):
        super()._initialize()

        self.fields = deepcopy(self.fields)

        offset = 0

        for field in self.fields.values():
            if isinstance(field, VariableBytesField):
                field.size = deepattr(self, field.related_field)

            field.offset = offset
            offset += field.size

        self.size = offset
