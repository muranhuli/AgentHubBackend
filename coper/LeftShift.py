from core.Computable import Computable


class LeftShift(Computable):
    def compute(self, x, y):
        return x << y
