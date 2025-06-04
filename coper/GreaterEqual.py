from core.Computable import Computable


class GreaterEqual(Computable):
    def compute(self, x, y):
        return x >= y
