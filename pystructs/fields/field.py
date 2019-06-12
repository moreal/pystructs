class Field:
    parent = None
    offset = 0

    def __init__(self, size: int):
        self.size = size

    def fetch(self):
        raise NotImplementedError()

    def is_root(self) -> bool:
        return self.parent is None
