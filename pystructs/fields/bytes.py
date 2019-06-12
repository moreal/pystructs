from pystructs.fields.field import Field


class BytesField(Field):
    def fetch(self) -> bytes:
        return self.parent.bytes[self.offset:self.offset+self.size]
