from pystructs.fields.struct import Struct
from pystructs.fields.bytes import BytesField


class CustomStruct(Struct):
    bytes_field = BytesField(4)


def test_bytes_field():
    assert CustomStruct(b'1234').bytes_field == b'1234'
