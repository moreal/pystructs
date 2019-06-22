import pytest

from pystructs.fields import BytesField, Struct


@pytest.fixture
def outer_struct():
    class InnerStruct(Struct):
        first = BytesField(size=4)
        second = BytesField(size=4)

    class OuterStruct(Struct):
        inner_struct = InnerStruct()

    outer_struct = OuterStruct(b'12345678')
    outer_struct.initialize()

    return outer_struct


def test_struct_can_have_recursive_struct(outer_struct):
    assert outer_struct.inner_struct.first == b'1234'


def test_struct_has_size_by_fields(outer_struct):
    assert outer_struct.inner_struct.size == 8
    assert outer_struct.size == 8


def test_struct_initialize_links_fields(outer_struct):
    inner_struct = outer_struct.inner_struct
    assert inner_struct.fields['second'].prev == inner_struct.fields['first']


def test_struct_getattr_raises_attribute_error(outer_struct):
    with pytest.raises(AttributeError):
        field = getattr(outer_struct, 'not_exists_field')
