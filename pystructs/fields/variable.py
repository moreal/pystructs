from functools import reduce
from typing import AnyStr

from pystructs.fields import BytesField, IntField, Field
from pystructs.interfaces import IVariable


class VariableBytesField(BytesField, IVariable):
    def __init__(self, related_field: AnyStr):
        self.related_field = related_field

