from core.Computable import Computable


class Greater(Computable):
    def compute(self, x, y):
        return x > y
