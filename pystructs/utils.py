from functools import reduce
from typing import AnyStr

from pystructs.fields import Field


def deepattr(obj: object, attrpath: AnyStr) -> object:
    return reduce(getattr, attrpath.split('.'), obj)


def filter_fields(attrs: dict) -> dict:
    attrs['fields'].update(dict(filter(lambda x: isinstance(x[1], Field), attrs.items())))
    return attrs


def delete_fields(attrs: dict) -> dict:
    for name in attrs['fields'].keys():
        if name in attrs:
            del attrs[name]
    return attrs
