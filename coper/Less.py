from core.Computable import Computable


class Less(Computable):
    def compute(self, x, y):
        return x < y
