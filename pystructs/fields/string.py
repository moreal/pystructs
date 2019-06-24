from typing import AnyStr

from pystructs.fields import BytesField


__all__ = [
    "StringField",
]


class StringField(BytesField):

    def __init__(self, size, encoding="utf8"):
        super().__init__(size)

        self.encoding = encoding

    def fetch(self) -> AnyStr:
        return super().fetch().decode(self.encoding)
