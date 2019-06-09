class Field:
    def __init__(self, _size: int):
        self.offset = 0
        self.size = _size

    def __get__(self, instance, owner):
        raise NotImplementedError()
