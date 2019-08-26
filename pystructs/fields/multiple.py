from copy import deepcopy
from typing import Union, AnyStr

from pystructs import utils
from pystructs.fields import Field, Struct


__all__ = [
    "MultipleField",
]


class MultipleField(Struct):
    def __init__(self, count: Union[int, AnyStr], field: Field):
        super().__init__(auto_initialization=False)

        if isinstance(count, int):
            self.count: int = count
        elif isinstance(count, str):
            self.count = -1
            self.related_field = count
        else:
            raise TypeError()

        self.field = field

    def initialize(self, root: Struct = None):
        if root is None:
            raise TypeError("MultipleField can't be root field")

        if self.count is -1:
            self.count = utils.deepattr(self.parent, self.related_field)

        self.fields = dict((i, deepcopy(self.field)) for i in range(self.count))

        super().initialize(root)

    def fetch(self) -> list:
        return list(self.fields.values())

