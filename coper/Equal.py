from core.Computable import Computable


class Equal(Computable):
    def compute(self, x, y):
        return x == y
