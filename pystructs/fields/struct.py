from copy import deepcopy
from typing import Dict, AnyStr

from pystructs import utils
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
        attrs = utils.filter_fields(attrs)
        offset = 0

        for name, field in attrs['fields'].items():
            if isinstance(field, IVariable):
                raise TypeError("ConstantStruct can't have `IVariable` Field")

            field.offset = offset
            offset += field.size

        attrs['size'] = offset

        return super().__new__(mcs, name, bases, attrs)


class VariableStructMetaclass(type):
    def __new__(mcs, name, bases, attrs: dict):
        attrs = utils.filter_fields(attrs)
        for name in attrs['fields'].keys():
            del attrs[name]
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


class ConstantStruct(Struct, IConstant, metaclass=ConstantStructMetaclass):
    pass


class VariableStruct(Struct, IVariable, metaclass=VariableStructMetaclass):
    def _initialize(self):
        super()._initialize()

        self.fields = deepcopy(self.fields)

        offset = 0

        for name, field in self.fields.items():
            field.offset = offset
            offset += field.size

        self.size = offset

    def __getattr__(self, item) -> Field:
        try:
            return self.fields[item].__get__(self, None)
        except KeyError:
            raise AttributeError(item)
