from pystructs.fields.bytes import BytesField


class IntField(BytesField):
    size = 4

    def __init__(self, byteorder='little'):
        self.byteorder = byteorder

    def __get__(self, instance, owner):
        return int.from_bytes(super().__get__(instance, owner), self.byteorder)


class Int32Field(IntField):
    size = 4


class Int64Field(IntField):
    size = 8
