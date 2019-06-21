import pytest

from pystructs.fields import BytesField, Struct


@pytest.fixture
def outer_struct():
    class InnerStruct(Struct):
        first = BytesField(4)

    class OuterStruct(Struct):
        inner_struct = InnerStruct()

    outer_struct = OuterStruct(b'1234')
    outer_struct.initialize()

    return outer_struct


def test_struct_can_have_recursive_struct(outer_struct):
    assert outer_struct.inner_struct.first == b'1234'


def test_struct_has_size_by_fields(outer_struct):
    assert outer_struct.inner_struct.size == 4
    assert outer_struct.size == 4

