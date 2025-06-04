from core.Computable import Computable


class RightShift(Computable):
    def compute(self, x, y):
        return x >> y
