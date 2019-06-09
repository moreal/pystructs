import pytest

from pystructs.fields.bytes import BytesField
from pystructs.fields.field import Field
from pystructs.fields.struct import Struct


class InnerStruct(Struct):
    first = BytesField(4)


class OuterStruct(Struct):
    inner_struct = InnerStruct()


def test_struct_can_have_recursive_stuct():
    outer_struct = OuterStruct(b'1234')
    assert outer_struct.inner_struct.first == b'1234'


def test_struct_has_size_by_fields():
    outer_struct = OuterStruct(b'')
    assert outer_struct.inner_struct.size == 4
    assert outer_struct.size == 4

