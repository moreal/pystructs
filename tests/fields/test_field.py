import pytest

from pystructs import fields


class CustomStruct(fields.Struct):
    first = fields.Field(2)
    second = fields.Field(2)


def test_field_will_raise_error():
    with pytest.raises(NotImplementedError):
        struct = CustomStruct(b'')
        struct.first


def test_field_set_offset_automatically():
    assert CustomStruct(b'').fields['first'].offset == 0
    assert CustomStruct(b'').fields['second'].offset == 2


def test_field_size():
    assert CustomStruct(b'').fields['first'].size == 2
    assert CustomStruct(b'').fields['second'].size == 2
