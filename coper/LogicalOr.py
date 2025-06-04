from core.Computable import Computable


class LogicalOr(Computable):
    def compute(self, x, y):
        return x or y
