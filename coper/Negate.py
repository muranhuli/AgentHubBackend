from core.Computable import Computable


class Negate(Computable):
    def compute(self, x):
        return -x