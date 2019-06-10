class Field:
    offset = 0

    def __init__(self, size: int):
        self.size = size

    def __get__(self, instance, owner):
        raise NotImplementedError()
