from __future__ import annotations
from copy import deepcopy
from typing import Dict, AnyStr, Union

from pystructs import utils
from pystructs.fields import BytesField, Field

__all__ = [
    'Struct',
]


class StructMetaclass(type):
    def __new__(mcs, name, bases, attrs: dict):
        attrs['fields'] = getattr(bases[0], 'fields', {}).copy()

        attrs = utils.filter_fields(attrs)
        attrs = utils.delete_fields(attrs)

        return super().__new__(mcs, name, bases, attrs)


class Struct(BytesField, metaclass=StructMetaclass):
    """
    `struct` implementations that inherit BytesField

    link fields and calculate offset and variable values automatically
    """

    #: Reflection of fields from struct
    fields: 'Dict[Union[AnyStr, int], Field]' = {}

    def __init__(self, _bytes: bytes = b'', auto_initialization=True):
        super().__init__(0)
        self.bytes = _bytes
        if auto_initialization:
            self.initialize()

    def fetch(self) -> 'Struct':
        return self

    def __getattr__(self, item):
        try:
            if item not in self.fields:
                return getattr(super(), item)
            return self.fields[item].fetch()
        except KeyError:
            raise AttributeError(item)

    def initialize(self, root: 'Struct' = None):
        """
        link fields and set parent, initialize each fields

        :param root: Struct object of root
        :return:
        """
        self.__link_fields()

        if root is None:
            root = self

        self.fields = deepcopy(self.fields)
        for field in self.fields.values():
            field.parent = self
            field.initialize(root)

    def __link_fields(self):
        fields = list(self.fields.values())
        fields_count = len(fields)

        for index in range(fields_count - 1):
            fields[index+1].prev = fields[index]

        if fields_count > 0:
            fields[0].prev = VirtualStruct(self)

    @property
    def size(self) -> int:
        return sum(map(lambda x: x.size, self.fields.values()))


class VirtualStruct:
    def __init__(self, struct: Struct):
        self.__struct = struct

    @property
    def offset(self) -> int:
        return self.__struct.offset

    @property
    def size(self) -> int:
        return 0
