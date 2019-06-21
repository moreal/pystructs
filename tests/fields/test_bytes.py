from pystructs import fields


class CustomStruct(fields.Struct):
    bytes_field = fields.BytesField(size=4)


def test_bytes_field():
    assert CustomStruct(b'1234').bytes_field == b'1234'
