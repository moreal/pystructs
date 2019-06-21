from pystructs import fields


class CustomStruct(fields.Struct):
    bytes_field = fields.BytesField(size=4)


def test_bytes_field():
    struct = CustomStruct(b'1234')
    struct.initialize()
    assert struct.bytes_field == b'1234'
