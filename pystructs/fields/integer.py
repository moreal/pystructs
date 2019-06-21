from pystructs.fields.bytes import BytesField


class IntField(BytesField):
    def __init__(self, size: int, byteorder='little'):
        super().__init__(size)
        self.byteorder = byteorder

    def fetch(self) -> int:
        return int.from_bytes(super().fetch(), self.byteorder)


class Int32Field(IntField):
    def __init__(self, **kwargs):
        super().__init__(4, **kwargs)


class Int64Field(IntField):
    def __init__(self, **kwargs):
        super().__init__(8, **kwargs)
