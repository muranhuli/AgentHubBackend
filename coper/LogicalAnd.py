from core.Computable import Computable


class LogicalAnd(Computable):
    def compute(self, x, y):
        return x and y
