from core.Computable import Computable


class LogicalNot(Computable):
    def compute(self, x):
        return not x