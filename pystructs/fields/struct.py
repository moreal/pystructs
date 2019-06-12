from copy import deepcopy
from typing import Dict, AnyStr, Union

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
        attrs = utils.delete_fields(attrs)

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
        attrs = utils.delete_fields(attrs)

        return super().__new__(mcs, name, bases, attrs)


class Struct(BytesField):
    fields: Dict[Union[AnyStr, int], Field]

    @property
    def bytes(self):
        return self._bytes

    def __init__(self, _bytes: bytes = b''):
        self._bytes = _bytes
        self._initialize()

    def fetch(self):
        self._bytes = self.parent.bytes[self.offset:self.offset+self.size]
        return self

    def __getattr__(self, item):
        try:
            return self.fields[item].fetch()
        except KeyError:
            raise AttributeError(item)

    def _initialize(self):
        self.fields = deepcopy(self.fields)
        self._initialize_parent_of_fields()

    def _initialize_parent_of_fields(self):
        for _, field in self.fields.items():
            field.parent = self


class ConstantStruct(Struct, IConstant, metaclass=ConstantStructMetaclass):
    pass


class VariableStruct(Struct, IVariable, metaclass=VariableStructMetaclass):
    def _initialize(self):
        self._initialize_parent_of_fields()
        self._calculate_offset_and_size()

    def _calculate_offset_and_size(self):
        offset = 0

        for name, field in self.fields.items():
            if isinstance(field, VariableStruct) and not field.is_root:
                field._initialize()

            field.offset = offset
            offset += field.size

        self.size = offset
