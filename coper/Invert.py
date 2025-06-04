from core.Computable import Computable


class Invert(Computable):
    def compute(self, x):
        return ~x