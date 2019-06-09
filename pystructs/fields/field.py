class Field:
    def __init__(self, size: int):
        self.offset = 0
        self.size = size

    def __get__(self, instance, owner):
        raise NotImplementedError()
