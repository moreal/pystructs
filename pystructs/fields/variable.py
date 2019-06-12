from functools import reduce
from typing import AnyStr

from pystructs.fields import BytesField, IntField, Field
from pystructs.interfaces import IVariable
from pystructs.utils import deepattr


class VariableBytesField(BytesField, IVariable):
    def __init__(self, related_field: AnyStr):
        self.related_field = related_field

    @property
    def size(self):
        return deepattr(self.parent, self.related_field)
