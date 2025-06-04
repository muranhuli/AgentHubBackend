from core.Computable import Computable


class NotEqual(Computable):
    def compute(self, x, y):
        return x != y
