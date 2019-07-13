from pystructs import fields


def test_int8_field_little_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int8Field(byteorder='little')

    struct = CustomStruct(b'\x01')
    struct.initialize()
    assert struct.field == 1


def test_int16_field_little_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int16Field(byteorder='little')

    struct = CustomStruct(b'\x01\x00')
    struct.initialize()
    assert struct.field == 1


def test_int16_field_big_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int16Field(byteorder='big')

    struct = CustomStruct(b'\x00\x01')
    struct.initialize()
    assert struct.field == 1


def test_int32_field_little_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int32Field(byteorder='little')

    struct = CustomStruct(b'\x01\x00\x00\x00')
    struct.initialize()
    assert struct.field == 1


def test_int32_field_big_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int32Field(byteorder='big')

    struct = CustomStruct(b'\x00\x00\x00\x01')
    struct.initialize()
    assert struct.field == 1


def test_int64_field_little_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int64Field(byteorder='little')

    struct = CustomStruct(b'\x01\x00\x00\x00\x00\x00\x00\x00')
    struct.initialize()
    assert struct.field == 1


def test_int64_field_big_byteorder():
    class CustomStruct(fields.Struct):
        field = fields.Int64Field(byteorder='big')

    struct = CustomStruct(b'\x00\x00\x00\x00\x00\x00\x00\x01')
    struct.initialize()
    assert struct.field == 1
