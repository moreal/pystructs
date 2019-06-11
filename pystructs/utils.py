from functools import reduce
from typing import AnyStr


def deepattr(obj: object, attrpath: AnyStr) -> object:
    return reduce(getattr, attrpath.split('.'), obj)
