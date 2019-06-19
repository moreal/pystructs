from pystructs.fields.field import Field


class BytesField(Field):
    @property
    def bytes(self):
        return self.__bytes[self.offset:self.offset+self.size]

    def fetch(self) -> bytes:
        return self.bytes
