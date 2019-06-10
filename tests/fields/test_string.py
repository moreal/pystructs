from pystructs import fields


def test_string_utf8_encoding():
    class CustomStruct(fields.ConstantStruct):
        string = fields.StringField(11, 'utf8')

    struct = CustomStruct(b'hello world')
    assert struct.string == 'hello world'


def test_string_ascii_encoding():
    class CustomStruct(fields.ConstantStruct):
        string = fields.StringField(11, 'ascii')

    struct = CustomStruct(b'hello world')
    assert struct.string == 'hello world'


def test_string_euckr_encoding():
    class CustomStruct(fields.ConstantStruct):
        string = fields.StringField(10, 'euc-kr')

    struct = CustomStruct(b'\xbe\xc8\xb3\xe7\xc7\xcf\xbc\xbc\xbf\xe4')
    assert struct.string == '안녕하세요'
