import pytest

from pystructs import fields
from pystructs.fields import Int32Field


@pytest.fixture
def constant_struct():
    class CustomStruct(fields.Struct):
        multiple_field = fields.MultipleField(4, fields.Int32Field())

    struct = CustomStruct(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    struct.initialize()

    return struct


@pytest.fixture
def variable_struct():
    class CustomStruct(fields.Struct):
        count = Int32Field(byteorder='big')
        multiple_field = fields.MultipleField("count", fields.Int32Field())

    struct = CustomStruct(b'\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01')
    struct.initialize()

    return struct


def test_multiple_field_set_size_automatically(constant_struct):
    assert constant_struct.size == 16


def test_multiple_field_returns_list(constant_struct):
    assert isinstance(constant_struct.multiple_field, list)


def test_multiple_field_can_be_variable(variable_struct):
    assert len(variable_struct.multiple_field) == variable_struct.count


