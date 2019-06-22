import pytest

from pystructs import fields
from pystructs.fields import Int32Field


@pytest.fixture
def struct():
    class CustomStruct(fields.Struct):
        count = Int32Field(byteorder='big')
        multiple_field = fields.MultipleField("count", fields.Int32Field())

    struct = CustomStruct(b'\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01')

    return struct


def test_multiple_field_set_size_automatically(struct):
    struct.initialize()
    assert struct.size == 20


def test_multiple_field_returns_list(struct):
    struct.initialize()
    assert isinstance(struct.multiple_field, list)


def test_multiple_field_can_be_variable(struct):
    struct.initialize()
    assert len(struct.multiple_field) == struct.count


def test_multiple_field_constructor_arguments():
    with pytest.raises(TypeError):
        fields.MultipleField(3.14, fields.Int32Field())


def test_multiple_field_cant_be_root():
    with pytest.raises(TypeError):
        field = fields.MultipleField(3, fields.Int32Field())
        field.initialize()
