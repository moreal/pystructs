from typing import AnyStr

from pystructs.fields import BytesField
from pystructs.utils import deepattr


__all__ = [
    "VariableBytesField"
]


class VariableBytesField(BytesField):
    def __init__(self, related_field: AnyStr):
        super().__init__(0)
        self.related_field = related_field

    @property
    def size(self):
        return deepattr(self.parent, self.related_field)
