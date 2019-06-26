from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pystructs.fields import Struct


__all__ = [
    "Field"
]


class Field:
    """
    Abstract class for parsing bytes by calculating offset and size variable
    """

    def __init__(self, size: int):
        self.parent: Struct = None
        self.__size: int = size
        self.__prev: Optional[Field] = None

    def fetch(self):
        """
        process to work value from bytes
        """
        raise NotImplementedError()

    def initialize(self, root: 'Field'):
        """
        process to initialize, eg. link_fields, set bytes of root field, etc...

        :param root: root field
        :type root: Field
        """

        raise NotImplementedError()

    @property
    def is_root(self) -> bool:
        """
        bool value about this field is root

        :type: bool
        """
        return self.__prev is None

    @property
    def prev(self) -> Field:
        """
        previous field of this, to be used in calculation offset

        :type: Field
        """
        return self.__prev

    @prev.setter
    def prev(self, field):
        self.__prev = field

    @property
    def offset(self) -> int:
        """
        offset of this

        :type: int
        """
        return 0 if self.is_root else (self.__prev.offset + self.__prev.size)

    @property
    def size(self) -> int:
        """
        size of this

        :type: int
        """
        return self.__size

    @property
    def parent(self) -> Field:
        """
        parent field of this, eg. Struct created by user

        :type: Field
        """
        return self.__parent

    @parent.setter
    def parent(self, value):
        self.__parent = value
