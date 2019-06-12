import copy
from copy import copy, deepcopy
from typing import Union, AnyStr

from pystructs import utils
from pystructs.fields import Field, VariableStruct
from pystructs.interfaces import IVariable


class MultipleField(VariableStruct, IVariable):
    def __init__(self, count: Union[int, AnyStr], field: Field):
        if isinstance(count, int):
            self.count: int = count
        elif isinstance(count, str):
            self.count = -1
            self.related_field = count
        else:
            raise TypeError()

        self.field = field

    def _initialize(self):
        super()._initialize_parent_of_fields()

        if self.count is -1:
            self.count = utils.deepattr(self.parent, self.related_field)

        self.fields = dict((i, deepcopy(self.field)) for i in range(self.count))
        self._calculate_offset_and_size()

    def fetch(self) -> list:
        return list(self.fields.values())

