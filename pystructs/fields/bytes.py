from pystructs.fields.field import Field


class BytesField(Field):
    def __get__(self, instance, owner):
        return instance.bytes[self.offset:self.offset+self.size]
