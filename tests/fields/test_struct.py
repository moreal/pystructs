import pytest

from pystructs.fields import (
    ConstantStruct,
    BytesField,
    VariableStruct)


@pytest.fixture
def outer_struct():
    class InnerStruct(ConstantStruct):
        first = BytesField(4)

    class OuterStruct(ConstantStruct):
        inner_struct = InnerStruct()

    return OuterStruct(b'1234')


def test_struct_can_have_recursive_struct(outer_struct):
    assert outer_struct.inner_struct.first == b'1234'


def test_struct_has_size_by_fields(outer_struct):
    assert outer_struct.inner_struct.size == 4
    assert outer_struct.size == 4


def test_constant_struct_can_have_only_constant_struct():
    with pytest.raises(TypeError):
        class Custom(ConstantStruct):
            inner_struct = VariableStruct()
