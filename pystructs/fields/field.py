from __future__ import annotations


class Field:
    __prev: Field
    __bytes: bytes  # bytes of root field
    __size: int

    def __init__(self, size: int):
        self.__size = size

    def fetch(self):
        raise NotImplementedError()

    @property
    def is_root(self) -> bool:
        return self.__prev is None

    @property
    def prev(self) -> Field:
        return self.__prev

    @prev.setter
    def prev(self, field):
        self.__prev = field

    @property
    def offset(self) -> int:
        return self.__prev.offset + self.__prev.size

    @property
    def size(self) -> int:
        return self.__size
