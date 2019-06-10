from pystructs import fields
from pystructs.fields.integer import Int32Field
from pystructs.fields.struct import Struct


def test_int32_field_little_byteorder():
    class CustomStruct(Struct):
        field = Int32Field(byteorder='little')

    struct = CustomStruct(b'\x01\x00\x00\x00')
    assert struct.field == 1


def test_int32_field_big_byteorder():
    class CustomStruct(Struct):
        field = Int32Field(byteorder='big')

    struct = CustomStruct(b'\x00\x00\x00\x01')
    assert struct.field == 1


def test_int64_field_little_byteorder():
    class CustomStruct(fields.ConstantStruct):
        field = fields.Int64Field(byteorder='little')

    struct = CustomStruct(b'\x01\x00\x00\x00\x00\x00\x00\x00')
    assert struct.field == 1


def test_int64_field_big_byteorder():
    class CustomStruct(fields.ConstantStruct):
        field = fields.Int64Field(byteorder='big')

    struct = CustomStruct(b'\x00\x00\x00\x00\x00\x00\x00\x01')
    assert struct.field == 1
