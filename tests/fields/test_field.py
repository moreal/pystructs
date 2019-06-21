import pytest

from pystructs import fields


class CustomStruct(fields.Struct):
    first = fields.Field(2)
    second = fields.Field(2)


def test_field_will_raise_error():
    with pytest.raises(NotImplementedError):
        struct = CustomStruct(b'')
        struct.initialize()
