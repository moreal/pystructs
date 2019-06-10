from typing import AnyStr

from pystructs.fields import BytesField


class StringField(BytesField):

    def __init__(self, size, encoding="utf8"):
        super().__init__(size)

        self.encoding = encoding

    def __get__(self, instance, owner) -> AnyStr:
        bytes = super().__get__(instance, owner)
        return bytes.decode(self.encoding)
