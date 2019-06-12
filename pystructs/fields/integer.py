from pystructs.fields.bytes import BytesField


class IntField(BytesField):
    size = 4

    def __init__(self, byteorder='little'):
        self.byteorder = byteorder

    def fetch(self) -> int:
        return int.from_bytes(super().fetch(), self.byteorder)


class Int32Field(IntField):
    size = 4


class Int64Field(IntField):
    size = 8
