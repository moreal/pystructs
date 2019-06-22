from pystructs.fields import Int32Field, Struct
from pystructs.fields.variable import VariableBytesField


def test_variable_bytes_field_has_variable_size():
    class CustomStruct(Struct):
        length = Int32Field(byteorder='big')
        data = VariableBytesField(related_field='length')

    struct = CustomStruct(b'\x00\x00\x00\x02\x12\x34')
    struct.initialize()

    assert struct.data == b'\x12\x34'
